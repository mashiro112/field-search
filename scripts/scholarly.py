#!/usr/bin/env python3
"""Bounded read-only scholarly metadata and relationship lookup.

No authentication, retries, crawling, PDF downloading, or semantic claim scoring.
Each command uses fixed public APIs and emits source URLs, provider failures,
coverage limits, and unknown states. See CLI --help for bounded commands.
"""
from __future__ import annotations
import argparse, json, re, sys, time
from datetime import datetime, timezone
from urllib import error, parse, request

USER_AGENT = "field-search-scholarly/1.0 (read-only; https://github.com/mashiro112/field-search)"
MAX_BYTES = 3_000_000
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
DOCS = {
 "crossref": {"api":"https://api.crossref.org/", "docs":"https://www.crossref.org/documentation/retrieve-metadata/rest-api/", "license":"Crossref metadata is openly available; individual member-deposited records may carry their own rights; metadata reuse attribution recommended."},
 "openalex": {"api":"https://api.openalex.org/", "docs":"https://docs.openalex.org/", "license":"OpenAlex data CC0; API availability and rate limits apply. This script uses anonymous API requests and no content-download service."},
 "europe_pmc": {"api":"https://www.ebi.ac.uk/europepmc/webservices/rest/", "docs":"https://europepmc.org/RestfulWebService", "license":"Europe PMC API is documented under Apache License 2.0; full-text article licenses vary by article and must be checked at source."},
 "datacite": {"api":"https://api.datacite.org/", "docs":"https://support.datacite.org/docs/api", "license":"Public API metadata retrieval requires no authentication; metadata and resource rights vary by record. API terms apply."}
}

class Client:
 def __init__(self, timeout=12, budget=4): self.timeout=timeout; self.budget=budget; self.calls=[]
 def get(self, url):
  if len(self.calls)>=self.budget: raise RuntimeError("request_budget_exhausted")
  if not url.startswith("https://") or not any(url.startswith(v["api"]) for v in DOCS.values()): raise RuntimeError("host_not_allowlisted")
  started=datetime.now(timezone.utc).isoformat(); t=time.monotonic(); row={"url":url,"started_at":started}
  req=request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
  try:
   with request.urlopen(req,timeout=self.timeout) as res:
    raw=res.read(MAX_BYTES+1); row.update(http_status=res.status,final_url=res.geturl(),elapsed_seconds=round(time.monotonic()-t,3),bytes=len(raw))
   if len(raw)>MAX_BYTES: raise RuntimeError("response_size_limit")
   payload=json.loads(raw.decode("utf-8")); row["status"]="ok"; self.calls.append(row); return payload
  except (error.HTTPError,error.URLError,TimeoutError,ValueError,RuntimeError) as e:
   if "elapsed_seconds" not in row: row["elapsed_seconds"]=round(time.monotonic()-t,3)
   row.update(status="error",error=type(e).__name__ if not isinstance(e,RuntimeError) else str(e)); self.calls.append(row); raise

def doi_norm(s):
 s=re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)\s*","",s.strip(),flags=re.I)
 if not DOI_RE.fullmatch(s): raise ValueError("invalid_doi")
 return s

def qurl(base, **params): return base+"?"+parse.urlencode(params)
def authors(xs): return [" ".join(x for x in (a.get("given"),a.get("family")) if x) for a in (xs or [])[:30]]
def norm_title(value): return " ".join((value or "").casefold().split())
def oa_work_id(value):
 return isinstance(value,str) and re.fullmatch(r"https://openalex\.org/W\d+",value) is not None

def oa_doi(value):
 if not isinstance(value,str): return ""
 value=parse.unquote(value.strip())
 value=re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)\s*","",value,flags=re.I)
 return value.rstrip("/").casefold()

def crossref_work(j):
 m=j.get("message",{}); return {"doi":m.get("DOI"),"title":(m.get("title") or [None])[0],"authors":authors(m.get("author")),"published":m.get("published-print",m.get("published-online",m.get("created",{}))).get("date-parts"),"type":m.get("type"),"container":(m.get("container-title") or [None])[0],"volume":m.get("volume"),"issue":m.get("issue"),"page":m.get("page"),"url":m.get("URL"),"license":m.get("license"),"relation":m.get("relation"),"link":m.get("link"),"update_to":m.get("update-to"),"is_referenced_by_count":m.get("is-referenced-by-count"),"source":"Crossref"}

def epmc_correction_metadata(hit):
 corrections=hit.get("commentCorrectionList")
 publication_types=hit.get("pubTypeList")
 retracted=hit.get("isRetracted")
 return {"commentCorrectionList":corrections,"commentCorrectionList_status":"declared" if corrections else "unknown",
         "pubTypeList":publication_types,"pubTypeList_status":"declared" if publication_types else "unknown",
         "isRetracted":retracted,"isRetracted_status":"declared" if retracted is not None else "unknown"}

def resolve(doi, title, c):
 out={"query":{"doi":doi,"title":title},"records":[],"provider_status":{}}
 if doi:
  d=doi_norm(doi); enc=parse.quote(d,safe="")
  for name,url in [("crossref",f"https://api.crossref.org/works/{enc}"),("openalex",qurl("https://api.openalex.org/works/https://doi.org/"+parse.quote(d,safe="/"))),("europe_pmc",qurl("https://www.ebi.ac.uk/europepmc/webservices/rest/search",query="DOI:"+d,format="json",resultType="core",pageSize=3))]:
   try:
    j=c.get(url)
    if name=="crossref":
     rec=crossref_work(j); rec["identity_match"]=str(rec.get("doi","")).casefold()==d.casefold()
     if not rec.get("doi") or not rec.get("title"): raise ValueError("crossref_required_identity_fields_missing")
    elif name=="openalex":
     rec={"doi":j.get("doi"),"identity_match":str(j.get("doi","")).removeprefix("https://doi.org/").casefold()==d.casefold(),"openalex_id":j.get("id"),"title":j.get("title"),"publication_year":j.get("publication_year"),"type":j.get("type"),"open_access":j.get("open_access"),"best_oa_location":j.get("best_oa_location"),"locations":[{"landing_page_url":z.get("landing_page_url"),"pdf_url":z.get("pdf_url"),"is_oa":z.get("is_oa"),"version":z.get("version"),"license":z.get("license"),"source_name":(z.get("source") or {}).get("display_name")} for z in j.get("locations",[])[:10]],"referenced_works":j.get("referenced_works",[])[:20],"cited_by_api_url":j.get("cited_by_api_url"),"source":"OpenAlex"}
     if not rec.get("openalex_id") or not rec.get("doi") or not rec.get("title"): raise ValueError("openalex_required_identity_fields_missing")
    else:
     if not isinstance(j.get("resultList"),dict) or not isinstance(j["resultList"].get("result"),list): raise ValueError("europe_pmc_result_list_missing")
     hits=j.get("resultList",{}).get("result",[]); rec={"hits":[{**{k:h.get(k) for k in ("id","source","pmid","pmcid","doi","title","authorString","pubYear","isOpenAccess","inEPMC","license","fullTextUrlList","supplementaryFiles") },**epmc_correction_metadata(h),"identity_match":str(h.get("doi","")).casefold()==d.casefold(),"attachments_status":"declared" if h.get("supplementaryFiles") else "unknown"} for h in hits[:3]],"source":"Europe PMC"}
    out["records"].append(rec); out["provider_status"][name]="ok" if (name!="europe_pmc" or rec["hits"]) else {"status":"empty","source_url":url}
   except Exception as e: out["provider_status"][name]={"status":"error","reason":str(e)}
 else:
  for name,base in [("crossref","https://api.crossref.org/works"),("openalex","https://api.openalex.org/works")]:
   try:
    url=qurl(base,**({"query":title,"rows":3,"select":"DOI,title,author,published,type,URL,container-title,update-to,relation,license"} if name=="crossref" else {"search":title,"per-page":3}))
    j=c.get(url)
    items=j.get("message",{}).get("items",[]) if name=="crossref" else j.get("results",[])
    out["records"] += [crossref_work({"message":x}) if name=="crossref" else {"doi":x.get("doi"),"openalex_id":x.get("id"),"title":x.get("title"),"publication_year":x.get("publication_year"),"type":x.get("type"),"open_access":x.get("open_access"),"source":"OpenAlex"} for x in items[:3]]; out["provider_status"][name]="ok" if items else {"status":"empty","source_url":url}
   except Exception as e: out["provider_status"][name]={"status":"error","reason":str(e)}
 return out

def execute(a):
 budget=a.request_budget; c=Client(a.timeout,budget); result={"schema_version":1,"tool":"field-search-scholarly","created_at":datetime.now(timezone.utc).isoformat(),"command":a.command,"sources":DOCS,"limitations":["Metadata and citation edges do not establish whether a cited work supports a claim.","OA indicators and links are discovery metadata; access, version and license must be confirmed at the landing page.","Unreturned records, missing relations or provider errors mean coverage is unknown, not absent.","No PDF/article body is fetched; use the existing document/report workflow on an explicitly selected public URL."],"network_calls":c.calls,"limits":{"request_budget":budget,"response_max_bytes":MAX_BYTES,"automatic_retries":False,"recursive_expansion":False}}
 try:
  if a.command=="resolve": result["resolution"]=resolve(a.doi,a.title,c)
  elif a.command=="edges":
   d=doi_norm(a.doi); work_url="https://api.openalex.org/works/https://doi.org/"+parse.quote(d,safe="/"); work=c.get(work_url); lim=min(a.limit,10)
   if not isinstance(work,dict): raise ValueError("openalex_work_response_schema_invalid")
   checks={"doi_matches":oa_doi(work.get("doi"))==d.casefold(),"id_is_canonical":oa_work_id(work.get("id")),"title_present":isinstance(work.get("title"),str) and bool(work.get("title"))}
   if not all(checks.values()): raise ValueError("openalex_work_identity_mismatch_or_missing:"+json.dumps(checks,separators=(",",":")))
   refs=work.get("referenced_works")
   if not isinstance(refs,list) or any(not oa_work_id(x) for x in refs): raise ValueError("openalex_reference_list_schema_invalid")
   work_id=work["id"].rsplit("/",1)[-1]
   result["paper"]={"doi":work.get("doi"),"id":work.get("id"),"title":work.get("title"),"source_url":work.get("doi"),"identity_check":"requested DOI equals returned DOI; returned OpenAlex ID has canonical W-id form"}
   result["references"]={"ids":refs[:lim],"returned":min(len(refs),lim),"reported_ids":len(refs),"truncated":len(refs)>lim,"coverage":"bounded_reference_id_sample_only" if len(refs)>lim else "complete_returned_reference_list","status":"ok","source_url":work_url}
   cb="https://api.openalex.org/works"
   if cb and len(c.calls)<budget:
    try:
     cite_url=qurl(cb,filter="cites:"+work_id,per_page=lim,cursor="*",select="id,doi,title,publication_year,type")
     j=c.get(cite_url); meta=j.get("meta") if isinstance(j,dict) else None; rows=j.get("results") if isinstance(j,dict) else None
     if not isinstance(meta,dict) or not isinstance(meta.get("count"),int) or not isinstance(rows,list) or any(not isinstance(x,dict) or not oa_work_id(x.get("id")) for x in rows): raise ValueError("openalex_citing_response_schema_invalid")
     next_cursor=meta.get("next_cursor")
     if next_cursor is not None and not isinstance(next_cursor,str): raise ValueError("openalex_cursor_schema_invalid")
     items=[{k:x.get(k) for k in ("id","doi","title","publication_year","type")} for x in rows[:lim]]
     result["citing_works"]={"items":items,"returned":len(items),"count":meta["count"],"next_cursor":next_cursor,"truncated":meta["count"]>len(items),"coverage":"first_cursor_page_sample_only" if meta["count"]>len(items) else "all_reported_citing_records_in_response","status":"ok","source_url":cite_url}
    except Exception as e: result["citing_works"]={"status":"error","reason":str(e)}
   else: result["citing_works"]={"status":"not_requested","reason":"request_budget_exhausted_or_endpoint_missing","coverage":"unknown"}
   result["citation_semantics"]="unknown_without_source_text"
  elif a.command=="resources":
   d=doi_norm(a.doi)
   relation_types=("IsCitedBy","IsReferencedBy","IsSupplementTo","IsSupplementedBy","Cites","References","HasPart","IsPartOf","IsDerivedFrom","IsSourceOf","IsVersionOf","HasVersion","IsPreviousVersionOf","IsNewVersionOf","Compiles","IsCompiledBy")
   relation_query="relatedIdentifiers.relationType:("+" OR ".join(relation_types)+")"
   query="relatedIdentifiers.relatedIdentifier:\""+d+"\" AND "+relation_query+" AND types.resourceTypeGeneral:(Dataset OR Software)"
   url=qurl("https://api.datacite.org/dois",query=query,**{"page[size]":min(a.limit,10)})
   try:
    j=c.get(url)
    if not isinstance(j.get("data"),list) or not isinstance(j.get("meta"),dict): raise ValueError("datacite_results_schema_invalid")
    items=[]
    for x in j.get("data",[])[:a.limit]:
     z=x.get("attributes",{}); matched=[r for r in (z.get("relatedIdentifiers") or []) if r.get("relatedIdentifierType")=="DOI" and r.get("relatedIdentifier","").removeprefix("https://doi.org/").casefold()==d.casefold() and r.get("relationType") in relation_types]
     if not matched: continue
     descriptions=(z.get("descriptions") or []); subjects=(z.get("subjects") or []); dates=(z.get("dates") or []); sizes=(z.get("sizes") or []); formats=(z.get("formats") or [])
     items.append({"doi":z.get("doi"),"title":(z.get("titles") or [{}])[0].get("title"),"creators":z.get("creators"),"publisher":z.get("publisher"),"publicationYear":z.get("publicationYear"),"version":z.get("version"),"types":z.get("types"),"rightsList":z.get("rightsList"),"descriptions":descriptions[:3],"descriptions_status":"declared" if descriptions else "unknown","subjects":subjects[:15],"subjects_status":"declared" if subjects else "unknown","dates":dates[:10],"dates_status":"declared" if dates else "unknown","sizes":sizes[:10],"sizes_status":"declared" if sizes else "unknown","formats":formats[:10],"formats_status":"declared" if formats else "unknown","matched_relatedIdentifiers":matched,"url":z.get("url"),"source_url":"https://doi.org/"+str(z.get("doi"))})
    total=j.get("meta",{}).get("total"); truncated=isinstance(total,int) and total>len(j.get("data",[])[:a.limit])
    result["resources"]={"items":items,"returned":len(items),"candidate_records_examined":len(j.get("data",[])[:a.limit]),"reported_total":total,"truncated":truncated,"coverage":"sampled_first_page; partial" if truncated else "all_reported_records_examined","relation_filter":relation_query,"record_type_filter":"Dataset OR Software","status":"ok","query_url":url}
   except Exception as e: result["resources"]={"status":"error","reason":str(e),"query_url":url}
   result["association_rule"]="Only DataCite Dataset/Software records with a returned relatedIdentifier matching the exact seed DOI and a documented relationType are treated as linked. Citation direction and relationType are preserved; title similarity is not used."
  elif a.command=="verify":
   d=doi_norm(a.doi); result["seed_doi"]=d; result["checks"]={}
   try:
    j=c.get("https://api.crossref.org/works/"+parse.quote(d,safe="")); m=j.get("message",{}); actual=(m.get("title") or [None])[0]
    result["checks"]["crossref_metadata"]={"status":"found","doi":m.get("DOI"),"identity_match":str(m.get("DOI","")).casefold()==d.casefold(),"title":actual,"type":m.get("type"),"update_to":m.get("update-to"),"relation":m.get("relation"),"published":m.get("published-print",m.get("published-online",{})).get("date-parts"),"source_url":m.get("URL")}
    if getattr(a,"expected_title",None): result["checks"]["expected_title_identity"]={"status":"matched" if norm_title(actual)==norm_title(a.expected_title) else "mismatched","expected":a.expected_title,"actual":actual,"comparison":"normalized case and whitespace exact match"}
    else: result["checks"]["expected_title_identity"]={"status":"not_requested"}
   except Exception as e: result["checks"]["crossref_metadata"]={"status":"not_found_or_unavailable","reason":str(e)}
   try:
    j=c.get(qurl("https://www.ebi.ac.uk/europepmc/webservices/rest/search",query="DOI:"+d,format="json",resultType="core",pageSize=3))
    if not isinstance(j.get("resultList"),dict) or not isinstance(j["resultList"].get("result"),list): raise ValueError("europe_pmc_verify_schema_invalid")
    hits=j["resultList"]["result"]; result["checks"]["europe_pmc"]={"status":"found" if hits else "not_found_in_this_index","hits":[{**{k:h.get(k) for k in ("doi","title","pubYear","isOpenAccess","inEPMC","license","fullTextUrlList","supplementaryFiles")},**epmc_correction_metadata(h),"identity_match":str(h.get("doi","")).casefold()==d.casefold(),"attachments_status":"declared" if h.get("supplementaryFiles") else "unknown"} for h in hits],"source_url":"https://europepmc.org/"}
   except Exception as e: result["checks"]["europe_pmc"]={"status":"not_found_or_unavailable","reason":str(e)}
   result["original_source_text_check"]={"status":"not_performed","reason":"Metadata cannot establish claim support; use an explicit article snapshot and inspect its source passage separately."}
   result["interpretation"]="Correction/retraction metadata checks and source-text inspection are separate. Indexed Crossref update/relation and Europe PMC records are not a guarantee of completeness. Verify publisher and registry notices for consequential use."
 except Exception as e: result["status"]="error"; result["error"]=str(e)
 result["network_calls"]=c.calls
 unhealthy=any(x.get("status")!="ok" for x in c.calls)
 for section in (result.get("resolution",{}).get("provider_status",{}),result.get("checks",{})):
  unhealthy=unhealthy or any((v.get("status") if isinstance(v,dict) else v) in ("error","empty","not_found_or_unavailable","not_found_in_this_index","mismatched") for v in section.values())
  unhealthy=unhealthy or any(isinstance(v,dict) and v.get("identity_match") is False for v in section.values())
 unhealthy=unhealthy or any(isinstance(v,dict) and v.get("status")=="error" for v in (result.get("citing_works"),result.get("resources")))
 unhealthy=unhealthy or bool(result.get("resources",{}).get("truncated"))
 if result.get("command")=="edges":
  refs=result.get("references",{}); citing=result.get("citing_works",{})
  unhealthy=unhealthy or refs.get("status")!="ok" or refs.get("truncated") is True or citing.get("status")!="ok" or citing.get("truncated") is True
 for rec in result.get("resolution",{}).get("records",[]):
  if rec.get("identity_match") is False or any(h.get("identity_match") is False for h in rec.get("hits",[])): unhealthy=True
 result["status"]=result.get("status","partial" if unhealthy else "ok")
 return result

def compact_summary(result, out_path):
 summary={"status":result.get("status"),"command":result.get("command"),"out":str(out_path),"request_count":len(result.get("network_calls",[])),"requests":[{"host":parse.urlsplit(x.get("url","")).hostname,"status":x.get("status"),"elapsed_seconds":x.get("elapsed_seconds")} for x in result.get("network_calls",[])]}
 if "resolution" in result:
  r=result["resolution"]
  summary["candidates"]=[{"source":x.get("source"),"doi":x.get("doi"),"title":x.get("title"),"identity_match":x.get("identity_match"),"open_access":x.get("open_access"),"oa_url":(x.get("best_oa_location") or {}).get("pdf_url") or (x.get("open_access") or {}).get("oa_url"),"europe_pmc_hits":[{"doi":h.get("doi"),"pmcid":h.get("pmcid"),"title":h.get("title"),"full_text_urls":[(u or {}).get("url") for u in (h.get("fullTextUrlList") or {}).get("fullTextUrl",[])[:2]],"attachments_status":h.get("attachments_status")} for h in x.get("hits",[])]} for x in r.get("records",[])]
  summary["provider_status"]=r.get("provider_status")
 if "paper" in result:
  summary["paper"]=result["paper"]; summary["reference_count"]=result.get("references",{}).get("reported_ids"); summary["reference_sample_count"]=result.get("references",{}).get("returned"); summary["reference_coverage"]=result.get("references",{}).get("coverage"); summary["citing_sample_count"]=result.get("citing_works",{}).get("returned"); summary["citing_count"]=result.get("citing_works",{}).get("count"); summary["citing_coverage"]=result.get("citing_works",{}).get("coverage"); summary["citing_next_cursor"]=result.get("citing_works",{}).get("next_cursor"); summary["citation_semantics"]=result.get("citation_semantics")
 if "resources" in result:
  rr=result["resources"]; summary["resource_count"]=rr.get("returned"); summary["resource_total"]=rr.get("reported_total"); summary["resource_coverage"]=rr.get("coverage"); summary["resources"]=[{"doi":x.get("doi"),"title":x.get("title"),"type":(x.get("types") or {}).get("resourceTypeGeneral"),"version":x.get("version"),"rights":[y.get("rights") for y in (x.get("rightsList") or [])],"description":[(y or {}).get("description") for y in (x.get("descriptions") or [])[:2]],"descriptions_status":x.get("descriptions_status","unknown"),"subjects":[(y or {}).get("subject") for y in (x.get("subjects") or [])[:8]],"subjects_status":x.get("subjects_status","unknown"),"dates":x.get("dates"),"dates_status":x.get("dates_status","unknown"),"sizes":x.get("sizes"),"sizes_status":x.get("sizes_status","unknown"),"formats":x.get("formats"),"formats_status":x.get("formats_status","unknown"),"relation":x.get("matched_relatedIdentifiers"),"url":x.get("source_url")} for x in rr.get("items",[])[:5]]
 if "checks" in result:
  summary["checks"]={k:{key:v.get(key) for key in ("status","identity_match","expected","actual","update_to","commentCorrectionList","commentCorrectionList_status","pubTypeList","pubTypeList_status","isRetracted","isRetracted_status") if key in v} for k,v in result["checks"].items()}
  if isinstance(result["checks"].get("europe_pmc"),dict):
   summary["checks"]["europe_pmc"]["correction_metadata_by_hit"]=[{k:h.get(k) for k in ("commentCorrectionList","commentCorrectionList_status","pubTypeList","pubTypeList_status","isRetracted","isRetracted_status")} for h in result["checks"]["europe_pmc"].get("hits",[])[:3]]
 if "original_source_text_check" in result: summary["original_source_text_check"]=result["original_source_text_check"]
 return summary

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="command",required=True)
 for name in ("resolve","edges","resources","verify"):
  s=sub.add_parser(name); s.add_argument("--doi"); s.add_argument("--limit",type=int,default=5); s.add_argument("--request-budget",type=int,default=4); s.add_argument("--timeout",type=float,default=12); s.add_argument("--out")
  if name=="resolve": s.add_argument("--title")
  if name=="verify": s.add_argument("--expected-title",help="Expected title for a normalized exact metadata identity comparison")
  if name in ("edges","resources","verify"):
   next(a for a in s._actions if a.dest=="doi").required=True
 a=p.parse_args(argv)
 if a.command=="resolve" and not (a.doi or a.title): p.error("resolve requires --doi or --title")
 if a.limit<1 or a.limit>10: p.error("--limit must be 1..10")
 if not 1<=a.request_budget<=8: p.error("--request-budget must be 1..8")
 if not 1<=a.timeout<=30: p.error("--timeout must be 1..30 seconds")
 if a.out and __import__("pathlib").Path(a.out).exists(): p.error("output_exists_choose_new_path")
 result=execute(a); out=json.dumps(result,ensure_ascii=False,indent=2)
 if a.out:
  from pathlib import Path
  path=Path(a.out)
  if path.exists(): p.error("output_exists_choose_new_path")
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open("x",encoding="utf-8",newline="\n") as f: f.write(out+"\n")
 sys.stdout.reconfigure(encoding="utf-8",errors="replace")
 print(json.dumps(compact_summary(result,a.out),ensure_ascii=False,indent=2) if a.out else out); return 0 if result["status"] in ("ok","partial") else 2
if __name__=="__main__": raise SystemExit(main())
