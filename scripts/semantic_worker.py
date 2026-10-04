"""FastEmbed multilingual semantic retrieval worker. Model/cache are task-local."""
from __future__ import annotations
import json, os, sys, time, traceback
from pathlib import Path

MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
DEFAULT_MIN_SCORE=0.30
CHUNK_SIZE=500
CHUNK_OVERLAP=100
MAX_CHUNKS=1000
def retrieve(query, docs, min_score=DEFAULT_MIN_SCORE):
    # Parent invokes this module with the dedicated R34 venv; never import a globally installed package.
    from fastembed import TextEmbedding
    import importlib.metadata
    if importlib.metadata.version('fastembed') != '0.7.3':
        raise RuntimeError('semantic_runtime_version_mismatch; tested FastEmbed version is 0.7.3')
    cache=Path(os.environ['FS_MODEL_DIR']).resolve(); cache.mkdir(parents=True,exist_ok=True)
    model_cached=any(p.stat().st_size>1_000_000 for p in cache.rglob('model_optimized.onnx') if p.exists())
    if not model_cached: raise RuntimeError('runtime_unavailable: model files missing from explicit --model-dir; automatic download is disabled')
    started=time.monotonic(); model=TextEmbedding(model_name=MODEL,cache_dir=str(cache),threads=2,local_files_only=True)
    chunks=[]; truncated_records=[]
    step=CHUNK_SIZE-CHUNK_OVERLAP
    for record_index,d in enumerate(docs):
        source=d['text']; starts=list(range(0,max(1,len(source)),step))
        for start in starts:
            if len(chunks)>=MAX_CHUNKS:
                truncated_records.append(d['artifact_id']); break
            end=min(len(source),start+CHUNK_SIZE)
            chunks.append((d,source[start:end],start,end))
        if len(chunks)>=MAX_CHUNKS:
            truncated_records.extend(x['artifact_id'] for x in docs[record_index+1:]); break
        if len(starts)>1 and len(chunks)>=MAX_CHUNKS: truncated_records.append(d['artifact_id'])
    texts=[c[1] for c in chunks]
    vecs=[]
    for offset in range(len(texts)):
        batch=texts[offset:offset+1]
        try: vecs.extend(model.embed(batch))
        except Exception as exc: raise ValueError(f'embed_batch_failed_at_record_{offset}: {type(exc).__name__}: {exc}; types={[type(x).__name__ for x in batch]}; first={[repr(x[:80]) for x in batch[:2]]}') from None
    q=list(model.query_embed(query))[0]
    import numpy as np
    sims=[]
    for i,v in enumerate(vecs):
        score=float(np.dot(q,v)/(np.linalg.norm(q)*np.linalg.norm(v)))
        sims.append((score,i))
    sims.sort(reverse=True); hits=[]
    best_score=sims[0][0] if sims else None
    for score,i in sims[:20]:
        if score < min_score: break
        d,chunk,start,end=chunks[i]
        # Preserve an inspectable supporting passage, not a model-authored answer.
        hit={'score_cosine':round(score,5),'artifact_id':d['artifact_id'],'kind':d['kind'],'path':d['path'],'url':d.get('url'),'hash':d.get('hash'),'snapshot_sha256':d.get('snapshot_sha256'),'where':d.get('where'),'record_index':d.get('record_index'),'excerpt':chunk[:700],'char_start':start,'char_end':end,'char_index_basis':'extracted_record_text_unicode_codepoints; end_exclusive'}
        loc=d.get('where') or {}; sec=loc.get('start_seconds') if isinstance(loc,dict) else None
        if d.get('kind')=='video' and isinstance(sec,(int,float)) and d.get('url'): hit['jump_url']=d['url']+('&' if '?' in d['url'] else '?')+'t='+str(int(sec))
        hits.append(hit)
    return hits,{'model':MODEL,'implementation':'FastEmbed/ONNX Runtime CPU; cosine similarity','model_cache':str(cache),'model_cache_hit':model_cached,'documents_embedded':len(chunks),'records_seen':len(docs),'chunk_chars':CHUNK_SIZE,'chunk_overlap':CHUNK_OVERLAP,'chunk_cap':MAX_CHUNKS,'truncated_artifacts':sorted(set(truncated_records)),'elapsed_seconds':round(time.monotonic()-started,3),'network_used':False,'minimum_retrieval_score':min_score,'best_score':round(best_score,5) if best_score is not None else None,'threshold_applied':True,'note':'Below-threshold means this model did not return candidates above the caller-selected retrieval threshold; it does not establish that the materials contain no answer. Scores are not truth guarantees; verify source text, and use literal find for exact identifiers. Truncated artifacts require literal find for complete coverage.'}

def main():
    try:
        if len(sys.argv)>1: req=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        else: req=json.load(sys.stdin)
        result=retrieve(req['query'],req['docs'],req.get('min_score',DEFAULT_MIN_SCORE)); print(json.dumps({'hits':result[0],'meta':result[1]},ensure_ascii=True))
    except Exception as e:
        print(json.dumps({'error':type(e).__name__+': '+str(e)[:200], 'trace':traceback.format_exc()[-1800:]},ensure_ascii=True)); raise SystemExit(2)
if __name__=='__main__': main()
