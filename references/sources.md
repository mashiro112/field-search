# Inspected methods and design choices

Initial inspection and integration: 2026-09-06. Links are provenance, not a frozen tool/model catalog. Check current documentation at the time of an actual integration. Remote text is reference material, not execution authority. The core instructions and adapters are original. Reviewed upstream modules and references are now bundled under `integrations/`, with original licenses, pinned commits and hashes in `integrations/provenance.json`. See [integration-map.md](integration-map.md) for exactly which collectors are called; bundling a project does not enable all its services.

| Upstream | Retained idea | Not adopted as a default |
|---|---|---|
| [last30days](https://github.com/mvanhorn/last30days-skill), [runtime skill](https://github.com/mvanhorn/last30days-skill/blob/main/skills/last30days/SKILL.md) | Cross-platform discovery; source health; reading community discussion | Fixed recency window, engagement as evidence strength, extensive output laws, automatic source setup |
| [Supersearch](https://github.com/glidea/supersearch-skills), [X adapter](https://github.com/glidea/supersearch-skills/blob/main/skills/x-search/scripts/search.mjs) | Separate source routes; Chinese communities; focused xAI X search | Treating xAI-backed search as Grok-independent access; installing every optional platform |
| [research-skill](https://github.com/hec-ovi/research-skill/blob/main/SKILL.md) | Source independence, strongest objection, concise findings with expandable evidence | Mandatory persistence/indexes, fixed model/delegation, 'latest' answers from unchecked old summaries |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/deep_researcher.py) | Explicit research brief, bounded iteration, research-specific evaluation | Always booting a separate agent server or parallel researcher tree |
| [Jina DeepResearch](https://github.com/jina-ai/node-DeepResearch/blob/main/src/agent.ts) | Search/read/reason loop focused on answering within budget | Unconditional external reasoning/reader service dependency |

## Official interfaces used by helpers

Additional research informing decision checks: [Adaptive-RAG](https://arxiv.org/abs/2403.14403) studies adapting retrieval effort to question complexity; [Sufficient Context](https://arxiv.org/abs/2411.06037) distinguishes relevant material from context that can answer the question. Field Search borrows these distinctions, not their trained models, implementations or benchmark gains. They motivate task-level checking; they do not validate this Skill's performance.

- [GitHub search](https://docs.github.com/en/rest/search), [issues](https://docs.github.com/en/rest/issues/issues), [issue comments](https://docs.github.com/en/rest/issues/comments).
- [HN search implementation/API](https://github.com/algolia/hn-search), [HN official API](https://github.com/HackerNews/API). Search relevance is Algolia's, not an evidence-quality judgment.
- [X post search](https://docs.x.com/x-api/posts/search/introduction). Developer access, quotas and billing differ from a Grok subscription.
- [xAI X Search](https://docs.x.ai/developers/tools/x-search). Requires API access and a compatible model.
- [Gemini Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search), [Gemini Deep Research](https://ai.google.dev/gemini-api/docs/deep-research), [API billing](https://ai.google.dev/gemini-api/docs/billing). The bundled grounded-search adapter is not the full Deep Research agent.
- [Codex skills](https://learn.chatgpt.com/docs/build-skills). Skills organize instructions, optional scripts and references; access comes from the host/tools, not the skill text itself.
