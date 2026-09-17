# Field Search

A search skill for finding reusable solutions and firsthand experience that can change the next action. It combines native search and reading with selected, task-driven collectors and document helpers.

This repository publishes the installed Skill source snapshot dated **2026-09-17** so ChatGPT and Codex can discuss the same implementation. It is not a claim that every provider or upstream workflow has been deployed, reproduced, or beaten.

## Read this in ChatGPT

Start with [CONTEXT_FOR_GPT.md](CONTEXT_FOR_GPT.md). Then read [the full first-party instruction bundle](docs/INSTRUCTIONS_FULL.md), followed by the implementations relevant to the question.

- [FS Skill full-picture guide](docs/FS-OVERVIEW.md) and [28-document history index](docs/history/INDEX.md): goals, evolution, experiments, bounded reviews, and academic research design
- [Academic evidence-to-writing SOP](docs/academic-evidence-to-writing/SOP.md): the current academic default, with [FS03 specification](docs/academic-evidence-to-writing/FS03-WORK-ITEM.md) and [reusable templates](docs/academic-evidence-to-writing/templates.md); specification complete, awaiting a real task trial
- [Skill entrypoint](SKILL.md)
- [Complete source index](docs/COMPLETE_SOURCE_INDEX.md): every one of the 162 original source files
- [Source manifest](SOURCE_MANIFEST.json): exact file sizes and SHA-256 hashes
- [Integration map](references/integration-map.md): installed code, adapted methods, and unavailable or external services
- [Provider/runtime notes](references/providers.md)
- [Upstream provenance](integrations/provenance.json)

The repository contains the full published source tree, not just a summary. A model opening one URL has not necessarily read every file. Ask it to state which files it actually read and which parts remain uninspected. The instruction bundle is convenient reading; it intentionally does not duplicate all upstream source code. Use the complete index or download the repository for the full implementation.

## Snapshot and runtime boundaries

All original source files in `SOURCE_MANIFEST.json` are byte-for-byte copies of the installed snapshot. Generated Python caches, credentials, login sessions, local research records, and external deployment environments are not included. Publication does not modify the installed Skill.

Some helpers depend on external runtimes or task-local adapters. The source preserves those references for an accurate snapshot; copying this repository alone does not recreate those deployments or grant account access. See `references/providers.md` before running a route. Provider availability, subscriptions, credentials, network access, and usage cost must be checked in the actual host environment.

The original upstream code includes optional collectors beyond the default routes. Their presence does not mean they are authorized, configured, or automatically invoked. In particular, authenticated or paid branches are not made available by this publication.

The owner has requested GitHub updates as part of every substantive FS development checkpoint and handoff. Follow [the development publication rules](AGENTS.md), keep the GPT entrypoint current, and identify the Git commit actually read. This repository contains the latest successfully published checkpoint; it does not mirror unsaved local edits through a background service.

## Licenses

Third-party license files and attribution are retained under `integrations/` and `THIRD_PARTY_NOTICES/`. See [LICENSES.md](LICENSES.md). This publication does not relicense third-party components or add a blanket license to original project material.
