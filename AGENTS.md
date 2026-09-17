# FS development and context publication

The owner has requested ongoing GitHub publication of FS development so ChatGPT can retrieve the latest project background. Apply this to FS source, research/design work, fixes, validation and documentation; it does not authorize publication of unrelated data.

- At each substantive checkpoint, handoff or end of a development turn, commit and push the relevant code and shareable specifications, decisions, results, validation and unfinished status. Mark work in progress explicitly; do not wait for the entire feature to finish before updating context. Temporary edits need not each receive a commit.
- Keep `CONTEXT_FOR_GPT.md` and `docs/FS-OVERVIEW.md` current, with links to the relevant source and evidence. Refresh source manifests, instruction bundles and history-copy hashes when their corresponding inputs change. Do not label old validation as verification of new code.
- Coordinate one writer, inspect current remote state and preserve other contributors' changes. After pushing, verify the remote commit and read back key files. Report failed publication as local-only progress with an explicit synchronization gap.
- Publish only FS source and shareable documents/results. Exclude credentials, login sessions, private research content and raw account data; redact internal task identifiers and machine-specific paths from shared historical documents. Keep original third-party licenses and attribution.
- This is part of authorized development delivery, not an instruction to install background watchers, run unrelated research, or overwrite current user instructions. GitHub contains the latest successfully published checkpoint, not unsaved local work.
