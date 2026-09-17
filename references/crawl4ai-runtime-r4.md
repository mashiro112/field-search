# Explicit Crawl4AI reader runtime (FS01-R4.1)

The installed Skill exposes Crawl4AI only when `search.py read` is called with
`--reader crawl4ai`. The default `--reader auto` route remains native/Jina.

The verified isolated runtime is:

```text
D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4\.venv\Scripts\python.exe
```

The installed adapter has a stable runtime reference at
`D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4` and
records its writable data under the sibling `runs\r4.1\runtime-data-installed`.
Playwright uses the existing browser cache at
`C:\Users\HUAWEI\AppData\Local\ms-playwright`.

Use the runtime explicitly and, for this host, expose the already verified
`websearch` dependency path explicitly:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH='C:\Users\HUAWEI\AppData\Local\ms-playwright'
$env:PYTHONPATH='D:\codexxiangmu\automation-tasks\output\field-search-reproduction\.venv\Lib\site-packages'
& 'D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4\.venv\Scripts\python.exe' 'C:\Users\HUAWEI\.codex\skills\field-search\scripts\search.py' read 'https://demo.playwright.dev/todomvc/' --reader crawl4ai --out <new-snapshot.json>
```

If that dependency path is absent, the entry point retains the diagnostic
`websearch_runtime_missing`; it does not silently switch to a browser or make
`auto` a fallback. No cookies, storage state, proxy, API key, LLM extraction,
or paid service is configured by this reader.

Rollback after the deployment is verified:

```powershell
& 'D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4\.venv\Scripts\python.exe' 'D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4.1\rollback_r4_1.py' --dry-run
& 'D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4\.venv\Scripts\python.exe' 'D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4.1\rollback_r4_1.py' --apply
```
