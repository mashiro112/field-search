# Evidence that supports a decision

Use these distinctions as judgment aids, not a numerical ranking formula or mandatory paperwork.

## A claim needs an origin and conditions

For each deciding claim retain, in prose or a small record:

- The claim and exactly what decision it affects.
- Original URL; author/role when known; publication/update date and retrieval date. Do not substitute retrieval time for publication time.
- Evidence type: official specification; firsthand report; independent reproduction; other synthesis; proposed hypothesis.
- Observed setup: version, OS, workload, sample, cost and relevant prerequisites. Unknown conditions remain unknown.
- Source excerpt, code location, artifact or measured observation that supports it. Keep quotes short and respect source limits. A provider's generated text is not an original source excerpt.
- Supporting and contradicting origin families, verification gaps, and what would reverse the finding.

Two URLs are not necessarily independent. Press coverage repeating a release, copied tutorials, a post linking a maintainer's statement, and two research models citing that statement share an origin. Conversely, one domain may host genuinely independent implementations. Track the causal origin of the evidence, not merely hostname counts.

Read enough of the surrounding thread to capture corrections and failure conditions. HN story titles and points establish neither successful use nor agreement in comments. A merged fix needs release/version verification before calling the bug fixed for the user. A closed issue can be duplicate, stale, wontfix or resolved.

## Retain useful exceptions without overvaluing novelty

Example (hypothetical): eight tutorials recommend tool A, all based on its Linux quickstart. One Windows user's reproducible issue identifies a required external binary. Do not say 'most sources favor A, therefore A is best'. Verify the requirement in current code/docs, check the fix/release, and compare with the user's environment. The minority report may change the action even if A remains generally capable.

Novel synthesis should have a traceable chain: observations -> proposed mechanism/combination -> expected benefit -> smallest test -> failure criterion. 'Not found in this search' is not 'never done before'. Recommending an existing feature can be the highest-value result.

For research claims, preserve study design, sample, uncertainty and population. Lived experience can reveal implementation barriers or generate hypotheses; it cannot by itself establish causal effectiveness or prevalence.

For research comparisons, distinguish a report or resource from its underlying study or analysis; record version, supplement, or derivation relationships only when relevant and supported by the source. If the relationship is unknown, preserve that uncertainty: do not merge reports by author/title alone or count them as independent evidence without a basis. For theoretical or methodological work, describe the proposition or method and its limits; retain empirical evidence when actually reported, but do not invent a sample, outcome, or validation. Apply the source-location rule above to decision-relevant interpretations of support, limitation, or challenge, including the conditions under which they hold.

## Compact work-item handoff example

Before delivery, check the few conditions that could reverse the recommendation against the evidence actually read. Keep this internal unless showing the condition helps the user. For a critical condition, retain: required fact → applicable support/counterevidence → unresolved part. Then distinguish:

- **Supported choice:** the deciding conditions have applicable support. State material limits; this is not a universal endorsement.
- **Conditional trial:** a candidate is promising, but a specific local dependency or workload result is unknown. State the condition, smallest discriminating test, and failure criterion. A test proposal is not a tested result.
- **Insufficient evidence to choose:** a deciding condition or conflict remains unresolved. Preserve useful discoveries and specify what could resolve the choice; do not select a winner from popularity or repeat counts.

Source status stays separate: `ok` means content was retrieved, `source_read` says how much was accessed, and neither determines these decision outcomes. A snippet may establish that a project exists while being insufficient to establish compatibility. If the same gap survives a batch, change the query, follow a dependency or original artifact, or propose a test rather than automatically expanding source count. URL deduplication also cannot prove independent origin families.

## Platform and resource boundaries

When the recommendation controls an operational action, preserve the boundary that the primary source actually supports:

- A dry-run, resolver check, metadata response or syntax check is a preflight result. It does not prove that an artifact was downloaded, installed, imported or exercised. State the additional success condition and keep the probe unrun when it was only proposed.
- Redirecting unbounded output to a temporary file avoids collecting all bytes in `communicate()` memory, but it does not impose a disk-byte limit. A later `max_bytes` read only limits the sample returned to the caller. A timeout must remain visible as a timeout outcome; do not fold it into an ordinary exit code.
- `run(timeout=...)` and `Popen.communicate(timeout=...)` have different cleanup semantics; neither is a general process-tree guarantee. Read the versioned subprocess documentation before giving a termination recipe.
- On Windows, confirm the platform implementation as well as the high-level API. `multiprocessing.Process.kill` aliases `terminate`; `ProcessPoolExecutor.terminate_workers()` and `kill_workers()` force shutdown and leave the pool unusable. Do not recommend a sequential terminate-then-kill escalation on one pool. `Future.cancel()` cannot stop a running call, and `shutdown(cancel_futures=True)` only removes work that has not started.

These checks are examples of evidence-backed condition handling, not a requirement to search Python documentation for every ordinary question. Apply them when the user's decision turns on a platform, resource, timeout or failure-state claim.

Adapt to the caller; do not force JSON on the user.

```json
{
  "decision": "Which existing approach fits the supplied constraints?",
  "recommendation": "A, conditional on the documented platform requirement",
  "why": ["Claim E1 resolves the required capability", "E2 excludes B for this setup"],
  "evidence": [
    {"id":"E1", "claim":"...", "url":"...", "kind":"official_spec",
     "conditions":"...", "verified":"page_read", "origin_family":"upstream-spec"}
  ],
  "conflicts": [],
  "coverage": {"web":"searched", "github":"searched_and_read", "x":"unavailable"},
  "tested": [],
  "unknowns": ["Performance on the user's workload is untested"],
  "next_action": "A scoped trial with a specified success condition"
}
```

Keep decisive exceptions in the compact return; expand supporting records only on demand. Coverage should identify the bounds (queries/date range/pages sampled) and distinguish unavailable, not attempted, no results and successfully searched. No forced percentage confidence.

## Evaluate improvements honestly

Use the same task, information access, model settings and time/tool-call budget when comparing a baseline, an existing skill and this workflow. Keep evaluation runs independent. Look for: deciding evidence recovered; viable reuse choices; appropriate conditions/counterexamples; citation correctness; unverified claims; executable next step; elapsed time/cost. A longer answer or more URLs alone is no gain.

If existing candidates could not be run, call the comparison a source/code audit, not a head-to-head benchmark. A small qualitative trial cannot establish universal superiority. Add only corrections supported by observed failures rather than endless new rules.

For iterative improvement, freeze the previous version before comparing, separate actual task performance from collector connectivity, and retain at least one task outside the failure that motivated a change. If both versions already make the right decision, report no demonstrated gain. If a task fails, identify whether the cause was retrieval, inaccessible evidence, applicability judgment, lost context, or an empirical uncertainty that search cannot resolve; modify the responsible layer only. Do not add automatic monitoring, private-history collection or global outcome storage just to make the skill appear self-improving.
