# Completed research report: DOM to private offline archive

R34 passed on one existing ChatGPT Deep Research report: 18 body headings,
4 tables/147 cells, 76 citation occurrences and 15 mapped sources, plus the
actual body ending. Archiving is lossless retention of the captured semantic
HTML and its links, not endorsement of the report's claims. No research job
was regenerated. Official download/Copy and OpenCLI result retrieval failed
in this host; the current native browser can read the rendered nested report.

## Capture only the visible report

Use the current task's native browser; a worker may not inherit its surfaces.
Inspect DOM first. In the tested layout the report is nested under
`iframe[title="深度研究"]` then `iframe#root`. Opening a rendered citation
expands the report; click a visible citation (`sup[data-citation-index]`) to
open its source panel. Current source entries are visible buttons labeled
`打开来源 N`, with ordinary source links. Rediscover selectors on UI changes.
Do not read React state, hidden conversation payloads, session tokens or private
backend APIs. Ordinary chat acknowledgements are not the research body.

The following is a read-only DOM recipe after those elements are observed.
Retain its result in the browser REPL variable, without printing the full body.
The headline's parent must be verified as the complete report container,
including its actual ending, before choosing it.

```javascript
const frame = tab.playwright.frameLocator('iframe[title="深度研究"]')
  .frameLocator('iframe#root');
const capture = await frame.locator('h1').evaluate((heading, sourceUrl) => {
  const root = heading.parentElement;
  const sources = Array.from(root.ownerDocument.querySelectorAll('button[aria-label^="打开来源 "]'))
    .map(button => {
      const match = button.getAttribute('aria-label').match(/打开来源\s+(\d+)/);
      const link = button.querySelector('a[href]');
      return match && link ? {index: Number(match[1]), label: link.textContent, url: link.href} : null;
    }).filter(Boolean);
  return {
    schema_version: 1, source_url: sourceUrl, html: root.innerHTML, sources,
    counts: {
      headings: root.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
      tables: root.querySelectorAll('table').length,
      table_cells: root.querySelectorAll('th,td').length,
      citation_occurrences: root.querySelectorAll('sup[data-citation-index]').length
    },
    method: 'rendered_report_dom_with_visible_source_panel'
  };
}, canonicalConversationUrl);
```

Some DOM bridges do not expose `ownerDocument`; use the same observed frame's
`body` locator to read its visible source buttons separately, then combine with
the report container. Do not guess missing sources. Semantic HTML may be
serialized without decoration; keep all text, headings, table cells, links and
citation indices, and compare counts with the rendered container.

## Save without model-body round trips

Start the one-shot local receiver (explicit private destination):

```text
<python> <skill-dir>/scripts/search.py capture --out <new-private-capture.json> --timeout 180
```

It binds only `127.0.0.1` on a random port, returns an expiring local URL, accepts
one form submission of at most 2 MB, saves exclusively and exits. It neither
uploads externally nor runs a daemon. Use its actual returned URL:

```javascript
const transfer = await cua.createBrowserTab('iab', receiverUrl, {visible:false});
await transfer.playwright.getByRole('textbox', {name:'Report capture JSON'})
  .fill(JSON.stringify(capture));
await transfer.playwright.getByRole('button', {name:'Save locally'}).click();
await transfer.getAXState(); // must show Saved locally
```

Confirm the receiver exited with `saved` and the local capture contains the
expected counts/source records. This handoff does not put the report body into
the language model's text context. On a host without browser access to loopback,
retain the failure and use a supported official export; do not silently send
private content through another service.

```text
search.py research-report <private-capture.json> --out-dir <new-private-archive>
search.py report find <private-archive>/report "<decisive phrase>"
search.py report open <private-archive>/report --page <ending-page>
```

The importer checks duplicate/missing citation indices, the declared HTML
structure and cached body hashes. Raw HTML remains authoritative for merged
cells, list nesting and special formatting. Keep warnings for malformed producer
URLs; a mapped citation is still unverified until its actual original supports
the claim. Save report body/capture only in the task's private area, not in FS
source, GitHub or automatic long-term memory.
