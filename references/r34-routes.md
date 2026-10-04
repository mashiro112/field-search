# R34: connected research and saved-material routes

The common entry is `<python> <skill-dir>/scripts/search.py`. New routes are
explicit tools selected for a real gap, not a mandatory fan-out. Use `--out`
where supported to retain full upstream records while printing a short summary.
No paid key, new model service or default monitor is involved.

## Scholarly originals, references and linked resources

```text
search.py scholarly resolve --doi 10.1056/NEJMoa2034577 --request-budget 3 --out <new.json>
search.py scholarly resolve --title "<paper title>" --request-budget 2 --out <new.json>
search.py scholarly edges --doi <seed-doi> --limit 3 --request-budget 2 --out <new.json>
search.py scholarly resources --doi <seed-doi> --limit 5 --request-budget 1 --out <new.json>
search.py scholarly verify --doi <doi> --expected-title "<cited title>" --request-budget 2 --out <new.json>
```

Crossref/OpenAlex establish candidate identities; Europe PMC supplies declared
OA links; DataCite returns Dataset/Software records with exact DOI relations.
Keep the relationship direction, individual version and rights. `resolve` does
not fetch a paper. Follow a selected public original with `read URL --out
<new-document.json>`, then `document find/open` offline. Use `convert` for an
explicit downloaded PDF and `ocr` for unreadable selected pages. Check the
decisive passage rather than treating citation edges or metadata as support.
Missing supplements mean unknown; no registered correction is not proof of
no correction. Title candidates and expected-title comparisons need judgment.
Budgets: 1–8 requests, 1–30 seconds each, 3 MB per response, at most 10 samples;
no retry or recursive expansion. Partial provider failures remain visible.

## Project review and public communities

```text
search.py context github-pr python/cpython 158584 --limit 20 --out <new.json>
search.py context github-discussion https://github.com/microsoft/vscode-discussions/discussions/1 --out <new.json>
search.py context community-search discourse "<query>" --limit 5 --out <new.json>
search.py context community-thread discourse https://discuss.python.org/t/<slug>/<id> --limit 20 --out <new.json>
search.py context community-search lemmy "<query>" --instance lemmy.world --page 1 --limit 5 --out <new.json>
search.py context community-thread lemmy <post-id> --instance lemmy.world --page 1 --limit 10 --out <new.json>
```

GitHub PR output includes reviews, inline/conversation comments, changed files
and patch, with per-collection limits and upstream pagination evidence. Public
Discussion extraction is the visible HTML sample, with unknown full-reply
coverage. Lemmy retains post/comment IDs, parent, text and source links;
returned comments can be fewer than a federated instance's reported total.
Continue only when `next_page` and the actual evidence gap justify it.
HN reuses the existing source. In R34, Bluesky's public route returned HTTP 403
and Linux.do required login; neither was counted as a successful new source.
[R35's browser route](r35-bluesky-web.md) is a separate Bluesky access path.
The owner has excluded Linux.do from current expansion work. The public
Lemmy route requires no account. `--full` is optional; default saved output
avoids emitting full discussions into model context.

## Explicit material sets, captions and semantic candidates

```text
search.py materials set <new-manifest.json> --artifact paper document <snapshot.json> --artifact report report <report-dir> --artifact talk video <captions.json>
search.py materials find <manifest.json> "<literal text or exact identifier>"
search.py materials semantic <manifest.json> "<paraphrase>" --model-dir <existing-model-cache> --min-score 0.30
search.py materials diff <old-document.json-or-report-dir> <new-document.json-or-report-dir>
```

Manifest `artifacts` entries contain only `id`, `kind`, `path`; relative paths
resolve against the manifest directory. Kinds: document, report, video, feed,
community, json. It scans only the chosen set (maximum 30 artifacts/64 MB).
Results retain source, saved hashes, exact text/location and video time links.
Failed artifacts are listed and make mixed results partial. Literal search
handles identifiers such as DOI, version and PEP number; use it before relying
on a semantic rank for those. No global directory or knowledge-base scan.

The optional runtime is `runtimes.semantic` in the existing local config, or
`--python-path <isolated-python>`; supply the model cache with `--model-dir` or
`runtimes.semantic.model_dir`. A runtime object can contain non-secret
`python_path` and `model_dir` paths; existing string entries still work.
Install FastEmbed 0.7.3 in that isolated runtime and acquire the named model
once explicitly. Retrieval uses `local_files_only=True`; missing model files
are an unavailable runtime, never an automatic download.
The tested engine is FastEmbed 0.7.3, ONNX CPU, multilingual MiniLM-L12-v2,
mean pooling. Long records use 500-character chunks/100 overlap, capped at
1,000 chunks with affected artifacts marked partial. The first installation downloaded roughly 235 MB; retrieval
uses the installed local model. No remote embedding/generative model is used.
Scores rank candidates, not truth or evidence strength. `below_threshold`
means this model supplied no candidate above the selected threshold; literal
search or another question may still find material. Report chunk bounds and
partial coverage rather than implying full semantic indexing.

Diff compares two saved originals once, keeps both, and reports changes or
extraction failure. `--ignore-line` suppresses explicitly chosen exact noise
lines; the receipt lists its normalization and filter. Inspect those filters
when wording or legal meaning matters. It starts no scheduled monitoring.

## Page OCR with original images

```text
search.py ocr <local.pdf-or-image> --pages 1,3-4 --out <new-report-dir>
search.py ocr <local.pdf> --pages 117 --region 0,0,0.48,1 --out <new-report-dir>
search.py report find <ocr-report-dir> "<term>"
```

`runtimes.ocr` or `--python-path` points to an isolated runtime containing
RapidOCR 3.9.2, ONNX Runtime and PyMuPDF. Example setup with that runtime:
`python -m pip install rapidocr==3.9.2 onnxruntime==1.30.0 PyMuPDF==1.28.2`.
Maximum 10 selected pages, 25 MB input, 24 million pixels/page, default 150 DPI
and 90-second subprocess timeout. Images and `ocr.json` preserve original PDF
page numbers, recognition boxes/confidence and hashes. Region coordinates are
normalized x0,y0,x1,y1; the complete page image is retained.
Reuse checks source/options, report, receipt and image hashes before skipping
OCR. Missing runtime or damaged captures do not silently overwrite results.
Chinese/English ordinary scans passed locating checks; historical vertical
Chinese, table cells, exponents and formulas are not faithful reconstruction.
Columns can interleave: use a selected region and the original image for
decisive numbers, claims and formulas.

## Existing ChatGPT reports

`research-report <capture.json> --out-dir <new-private-archive>` imports a real
rendered report capture, validates declared structure/citation mappings, keeps
raw HTML and report hashes, and feeds the existing offline `report open/find`.
See [research-report-dom.md](research-report-dom.md) for the tested browser
capture and one-shot loopback handoff. No new research job is required for
archiving an existing answer. Unmapped citations/structure mismatch are partial;
producer-invalid source URLs remain verbatim and visibly unverified.

## Datasets, patents and regulatory originals

Datasets: use `scholarly resources`, then read the resource's registered
description, version, rights and related study. Registration is not a license
grant and finding a record is not a successful data-file download.

US federal publications have an actual keyless adapter:

```text
search.py federal-register search "<topic>" --type RULE --limit 3 --out <new.json>
search.py federal-register read 2017-01058 --report-out <new-report-dir> --out <new.json>
```

Keep Rule/Proposed Rule/Notice distinct, jurisdiction explicit and publication
date separate from effective date. The informational XML/text rendition links
the official govinfo PDF; current applicability/validity is not established by
this adapter. Other jurisdictions use selected official sources and existing
`read`, not this US-specific API.

Patents: native web search finds the exact publication ID/kind and publisher
PDF link. Download that explicit PDF, then `convert <local.pdf> --source-url
<publication-url> --out-dir <report-dir>`; use `ocr` on missing claims or
correction pages. The two tested US patent PDFs are readable through this
combination, while Google Patents' automated-query interstitial is rejected as
an access gate, including old poisoned snapshots. Preserve publication and
application IDs; inspect correction notices and the relevant official registry
for current rights. This adds no paid patent API or blanket legal conclusion.

## Reuse provenance

Direct runtimes: [FastEmbed](https://github.com/qdrant/fastembed) (Apache-2.0),
[multilingual MiniLM model](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
(model's own Apache-2.0 license), [RapidOCR](https://github.com/RapidAI/RapidOCR)
(Apache-2.0), [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (AGPL/commercial),
existing MarkItDown and report/document readers. Dependencies retain their own
licenses; binaries/models are not vendored in FS. OCR and embeddings execute
locally; API/UI boundaries remain separate.

Thin FS-owned adaptation uses the documented
[Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/),
[OpenAlex](https://docs.openalex.org/), [Europe PMC](https://europepmc.org/RestfulWebService),
[DataCite](https://support.datacite.org/docs/api),
[GitHub REST](https://docs.github.com/en/rest/pulls),
[Lemmy API](https://join-lemmy.org/api/) and
[Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1).
This is runtime/API integration and small format glue, not copying a research
platform or installing more rule-only Skills.
