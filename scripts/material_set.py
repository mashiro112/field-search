"""Offline retrieval and one-shot comparison over an explicit set of saved FS artifacts."""
from __future__ import annotations
import argparse, hashlib, json, re, sys, unicodedata, subprocess, os, uuid, tempfile
from pathlib import Path
from typing import Any

MAX_ITEMS, MAX_BYTES = 30, 64 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]

def manifest(path: str) -> list[dict[str, str]]:
    p=Path(path).expanduser().resolve()
    if p.stat().st_size > 1024*1024: raise ValueError('manifest_too_large')
    obj=json.loads(p.read_text(encoding='utf-8-sig')); rows=obj.get('artifacts') if isinstance(obj,dict) else None
    if not isinstance(rows,list) or not 1 <= len(rows) <= MAX_ITEMS: raise ValueError('artifacts_must_be_1_to_30_items')
    out=[]; seen=set()
    for x in rows:
        if not isinstance(x,dict) or set(x)-{'id','kind','path'} or not {'id','kind','path'} <= set(x): raise ValueError('invalid_artifact_entry')
        if not all(isinstance(x[k],str) and x[k].strip() for k in ('id','kind','path')) or x['id'] in seen: raise ValueError('invalid_artifact_identity')
        if len(x['id'])>80 or len(x['path'])>4096 or any(ord(c)<32 for c in x['id']): raise ValueError('artifact_identity_or_path_too_long')
        if x['kind'] not in {'document','report','video','feed','community','json'}: raise ValueError('unsupported_kind')
        pth=Path(x['path']).expanduser(); pth=pth if pth.is_absolute() else p.parent/pth
        out.append({'id':x['id'],'kind':x['kind'],'path':str(pth.resolve())}); seen.add(x['id'])
    return out

def _text_records(item):
    p=Path(item['path']); kind=item['kind']; data=json.loads(p.read_text(encoding='utf-8-sig')) if kind!='report' else None
    snap_hash=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    if kind=='document':
        import document
        d=document.load_document(str(p)); return [{'text':d['content'],'url':d.get('url'),'hash':d.get('content_sha256'),'snapshot_sha256':snap_hash,'where':'document'}]
    if kind=='report':
        import report
        _,_,_,meta,body=report._resolve_report(str(p)); return [{'text':body,'url':(meta.get('source') or {}).get('url'),'hash':(meta.get('report') or {}).get('sha256'),'snapshot_sha256':hashlib.sha256((p/'report.md').read_bytes()).hexdigest(),'where':'report'}]
    if not isinstance(data,dict): raise ValueError('artifact_json_not_object')
    if kind=='video':
        if data.get('status') not in {'ok','partial'}: raise ValueError('saved_video_status_'+str(data.get('status','missing')))
        rec=data.get('records');
        if not isinstance(rec,list): raise ValueError('video_records_missing')
        return [{'text':str(x.get('text','')),'url':data.get('url'),'hash':None,'where':{'start_seconds':x.get('start_seconds'),'end_seconds':x.get('end_seconds'),'index':x.get('index')}} for x in rec if isinstance(x,dict) and x.get('text')]
    if kind=='feed':
        es=data.get('entries');
        if not isinstance(es,list): raise ValueError('feed_entries_missing')
        return [{'text':'\n'.join(str(e.get(k,'')) for k in ('title','summary','content')),'url':e.get('link') or data.get('source_final'),'hash':data.get('content_sha256'),'where':{'entry_id':e.get('id'),'date':e.get('date')}} for e in es if isinstance(e,dict)]
    if kind=='community':
        rs=data.get('records') or data.get('posts') or data.get('results')
        if not isinstance(rs,list): raise ValueError('community_records_missing')
        return [{'text':'\n'.join(str(x.get(k,'')) for k in ('title','text','raw','cooked','content','body')),'url':x.get('url'),'hash':None,'where':{'post_id':x.get('post_id') or x.get('id')}} for x in rs if isinstance(x,dict)]
    # generic JSON is intentionally narrow: only declared text-bearing records
    rs=data.get('records') or data.get('entries') or data.get('posts') or data.get('results')
    if not isinstance(rs,list): raise ValueError('json_text_records_missing')
    return [{'text':'\n'.join(str(x.get(k,'')) for k in ('title','text','content','summary','body')),'url':x.get('url') or x.get('link'),'hash':None,'where':{'id':x.get('id')}} for x in rs if isinstance(x,dict)]

def load(items):
    material=[]; failures=[]; total=0
    for it in items:
        try:
            if Path(it['path']).stat().st_size > MAX_BYTES: raise ValueError('artifact_too_large')
            rs=_text_records(it)
            good=[r for r in rs if r.get('text','').strip()]
            if not good: raise ValueError('no_text_records')
            artifact_file=Path(it['path'])
            snapshot_digest=hashlib.sha256(artifact_file.read_bytes()).hexdigest() if artifact_file.is_file() else None
            for n,r in enumerate(good):
                r.update(artifact_id=it['id'],kind=it['kind'],path=it['path'],record_index=n,snapshot_sha256=r.get('snapshot_sha256') or snapshot_digest)
                total+=len(r['text'].encode('utf-8'))
                if total>MAX_BYTES: raise ValueError('total_scan_budget_exceeded')
                material.append(r)
        except Exception as e: failures.append({'id':it['id'],'reason':str(e)[:120] or 'artifact_invalid'})
    return material,failures

def _result(x,start,end,query):
    text=x['text']; out={k:x.get(k) for k in ('artifact_id','kind','path','url','hash','snapshot_sha256','where','record_index')} | {'excerpt':text[max(0,start-140):min(len(text),end+220)],'exact':text[start:end],'char_start':start,'char_end':end,'char_index_basis':'extracted_record_text_unicode_codepoints; end_exclusive','query':query}
    loc=x.get('where') or {}; sec=loc.get('start_seconds') if isinstance(loc,dict) else None
    if x.get('kind')=='video' and isinstance(sec,(int,float)) and x.get('url'):
        out['jump_url']=x['url']+('&' if '?' in x['url'] else '?')+'t='+str(int(sec))
    return out

def find(manifest_path,query,semantic=False,min_score=0.30,python_path=None,model_dir=None,config_path=None):
    if not query.strip() or len(query)>500 or any(ord(c)<32 for c in query): raise ValueError('query_must_be_1_to_500_printable_chars')
    items=manifest(manifest_path); docs,failures=load(items)
    if semantic:
        if not 0 <= min_score <= 1: raise ValueError('min_score_must_be_between_0_and_1')
        if not docs: return {'status':'no_candidates','mode':'fastembed_multilingual','query':query,'hits':[],'failures':failures,'semantic':{'minimum_retrieval_score':min_score},'network_used':False}
        import runtime_config
        config_result=runtime_config.load_config(config_path)
        selected=python_path or runtime_config.runtime_path(config_result.get('data') or {},'semantic')
        if not selected: raise RuntimeError('semantic_runtime_unconfigured; supply --python-path or runtimes.semantic in local config')
        py=Path(selected).expanduser()
        if not py.is_file(): raise RuntimeError('semantic_runtime_missing')
        semantic_entry=(config_result.get('data') or {}).get('runtimes',{}).get('semantic')
        model_dir=model_dir or (semantic_entry.get('model_dir') if isinstance(semantic_entry,dict) else None)
        if not model_dir: raise RuntimeError('semantic_model_dir_required; supply --model-dir or runtimes.semantic.model_dir')
        model_path=Path(model_dir).expanduser().resolve()
        env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','SSL_CERT_FILE','SSL_CERT_DIR','HTTP_PROXY','HTTPS_PROXY','NO_PROXY'}}
        env.update(PYTHONIOENCODING='utf-8',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',FS_MODEL_DIR=str(model_path),FASTEMBED_CACHE_PATH=str(model_path))
        req_path=Path(tempfile.gettempdir())/f'field-search-semantic-{uuid.uuid4().hex}.json'
        req_path.write_text(json.dumps({'query':query,'docs':docs,'min_score':min_score},ensure_ascii=False),encoding='utf-8')
        try: cp=subprocess.run([str(py),'-I','-B',str(Path(__file__).with_name('semantic_worker.py')),str(req_path)],encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,env=env)
        except subprocess.TimeoutExpired: raise RuntimeError('semantic_worker_timeout_180s') from None
        finally: req_path.unlink(missing_ok=True)
        try: val=json.loads(cp.stdout)
        except json.JSONDecodeError: raise RuntimeError('semantic_worker_invalid_json') from None
        if cp.returncode or val.get('error'): raise RuntimeError((val.get('error','semantic_worker_failed')+'; '+val.get('trace','')+'; '+cp.stderr[-250:])[:1000])
        hits,meta=val['hits'],val['meta']
        return {'status':('partial' if failures or meta.get('truncated_artifacts') else 'ok') if hits else ('partial' if failures or meta.get('truncated_artifacts') else 'below_threshold'),'mode':'fastembed_multilingual','query':query,'hits':hits,'failures':failures,'semantic':meta,'network_used':meta.get('network_used')}
    hits=[]; q=query.casefold()
    for d in docs:
        pos=0; original=d['text']; folded=[]; char_map=[]
        for original_index,char in enumerate(original):
            unit=char.casefold(); folded.append(unit); char_map.extend([original_index]*len(unit))
        low=''.join(folded)
        while (i:=low.find(q,pos))>=0:
            start=char_map[i]; end=char_map[i+len(q)-1]+1
            hits.append(_result(d,start,end,query)); pos=i+max(1,len(q))
            if len(hits)>=100: break
        if len(hits)>=100: break
    return {'status':('partial' if failures else 'ok') if hits else ('partial' if failures else 'no_results'),'mode':'literal_case_insensitive','query':query,'hits':hits[:30],'total_hits':len(hits),'indexed_records':len(docs),'total_artifacts':len(items),'truncated':len(hits)>30,'failures':failures,'network_used':False}

def diff(old_path,new_path,ignore_lines=None):
    def extract(path):
        path=Path(path)
        if path.is_file() and path.stat().st_size>MAX_BYTES: return None,'error','snapshot_too_large'
        if path.is_dir():
            import report
            try: _,_,_,meta,body=report._resolve_report(str(path))
            except (OSError,UnicodeError,json.JSONDecodeError,KeyError,TypeError,ValueError) as exc: return None,'error',str(exc)[:160] or 'report_snapshot_invalid'
            if meta.get('status') not in {'ok','partial'}: return None,meta.get('status'),meta.get('reason')
            return body,'ok',None
        try:
            import document
            doc=document.load_document(str(path))
            return doc['content'],'ok',None
        except (OSError,ValueError,KeyError,TypeError,UnicodeError): pass
        try: x=json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,UnicodeError,json.JSONDecodeError): return None,'error','snapshot_unreadable_or_invalid_json'
        if not isinstance(x,dict): return None,'error','snapshot_not_object'
        # Recognized document extraction snapshots must never fall back to treating
        # their metadata, login gate, or damaged schema as extracted prose.
        if any(k in x for k in ('content_sha256','extraction')):
            return None,'error','recognized_document_snapshot_failed_validation'
        if x.get('status') not in (None,'ok','partial'): return None,x.get('status'),x.get('reason')
        es=x.get('entries')
        if isinstance(es,list): return '\n'.join('\n'.join(str(e.get(k,'')) for k in ('title','summary','content')) for e in es if isinstance(e,dict)),'ok',None
        for k in ('content','text','body','markdown'):
            if isinstance(x.get(k),str): return x[k],'ok',None
        return None,x.get('status','error'),x.get('reason','extractable_text_missing')
    at,astat,areason=extract(old_path); bt,bstat,breason=extract(new_path)
    if at is None or bt is None: return {'status':'extraction_failed','old_status':astat,'new_status':bstat,'old_reason':areason,'new_reason':breason,'old_snapshot':str(Path(old_path).resolve()),'new_snapshot':str(Path(new_path).resolve()),'old_preserved':True,'new_preserved':True,'network_used':False}
    # Navigation chrome is usually HTML; strip tags and common volatile nav/footer lines.
    ignored={unicodedata.normalize('NFKC',' '.join(x.split())).casefold() for x in ['skip to content','privacy policy','terms of service','all rights reserved','cookie settings']}
    ignored.update(unicodedata.normalize('NFKC',' '.join(x.split())).casefold() for x in (ignore_lines or []))
    def clean(s):
        s=re.sub(r'<(script|style)\b[^>]*>.*?</\1>',' ',s,flags=re.I|re.S)
        s=re.sub(r'</?(?:html|body|div|p|section|article|ul|ol|li|table|thead|tbody|tr|th|td|a|span|br|strong|em|h[1-6])(?:\s[^>]*|/?)>',' ',s,flags=re.I); lines=[]
        for line in s.splitlines():
            t=' '.join(line.split()); low=t.casefold()
            if not t or low in ignored: continue
            lines.append(t)
        return '\n'.join(lines)
    old,new=clean(at),clean(bt); oldn,newn=unicodedata.normalize('NFC',old),unicodedata.normalize('NFC',new)
    if oldn==newn: state='no_material_change'
    else: state='content_changed'
    # bounded line-level change summary
    al,bl=oldn.splitlines(),newn.splitlines(); aset,bset=set(al),set(bl)
    removed_all=[x for x in al if x not in bset]; added_all=[x for x in bl if x not in aset]
    removed,added=removed_all[:20],added_all[:20]
    return {'status':state,'old_snapshot':str(Path(old_path).resolve()),'new_snapshot':str(Path(new_path).resolve()),'old_preserved':True,'new_preserved':True,'old_sha256':hashlib.sha256(oldn.encode()).hexdigest(),'new_sha256':hashlib.sha256(newn.encode()).hexdigest(),'removed_lines':removed,'added_lines':added,'change_summary_truncated':len(removed_all)>20 or len(added_all)>20,'navigation_filter':{'exact_ignored_lines':sorted(ignored),'normalization':'NFC; horizontal whitespace; explicit HTML tags only'},'network_used':False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('set',help='create a new explicit task-local material manifest'); s.add_argument('manifest'); s.add_argument('--artifact',action='append',nargs=3,metavar=('ID','KIND','PATH'),required=True)
    for name in ('find','semantic'):
        q=sub.add_parser(name); q.add_argument('manifest'); q.add_argument('query')
        if name=='semantic':
            q.add_argument('--min-score',type=float,default=0.30,help='minimum cosine retrieval score 0..1; filters model candidates only')
            q.add_argument('--python-path',help='isolated Python runtime with FastEmbed installed')
            q.add_argument('--model-dir',help='task-local FastEmbed model/cache directory')
            q.add_argument('--config',help='local field-search runtime config with runtimes.semantic')
    d=sub.add_parser('diff'); d.add_argument('old_snapshot'); d.add_argument('new_snapshot'); d.add_argument('--ignore-line',action='append',default=[],help='exact normalized navigation line to ignore; may be repeated')
    a=p.parse_args(argv)
    try:
        if a.cmd=='set':
            target=Path(a.manifest).expanduser().resolve()
            rows=[{'id':i,'kind':k,'path':path} for i,k,path in a.artifact]
            if target.exists(): raise ValueError('manifest_already_exists')
            if len(rows)>MAX_ITEMS: raise ValueError('artifacts_must_be_1_to_30_items')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps({'artifacts':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            try: manifest(str(target))
            except Exception:
                target.unlink(missing_ok=True); raise
            out={'status':'ok','manifest':str(target),'artifacts':len(rows),'network_used':False}
        elif a.cmd=='diff': out=diff(a.old_snapshot,a.new_snapshot,a.ignore_line or None)
        else: out=find(a.manifest,a.query,a.cmd=='semantic',getattr(a,'min_score',0.30),getattr(a,'python_path',None),getattr(a,'model_dir',None),getattr(a,'config',None))
    except Exception as e: out={'status':'error','reason':str(e)[:1000],'network_used':False}
    print(json.dumps(out,ensure_ascii=False)); return 0 if out['status'] in {'ok','no_results','partial','below_threshold','no_candidates','content_changed','no_material_change'} else 2
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
