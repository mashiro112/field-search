> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# R22 installed thin integration result

## Outcome

Installed `field-search` now exposes one explicit `scripts/search.py xiaohongshu` route. It forwards only bounded `search` and `feed` calls to the verified R22 read-only adapter. The ordinary `doctor`, `search`, `read`, `auto`, and cross-source fan-out paths were not changed.

The first installed live attempt was rejected as `decode_error` because the adapter process could still emit console-default bytes on a Windows pipe. The isolated adapter entry now configures worker/CLI stdout as strict UTF-8; the outer bridge still rejects any invalid stdout without exposing bytes. The frozen live files remain unchanged and their decoder recheck passes.

## Installed live acceptance

The same authorized isolated session and keyword were used once through the installed entry after the encoding fix:

- Search: `status=ok`, requested limit `1`, actual `returned_count=1`, `output_truncated=false`, worker return code `0`, `timed_out=false`, `cleanup=null`.
- Feed: `status=ok`, opaque reference `r22:[public-example-ref-omitted]`, target `1`, actual `returned_items=18`, `top_level_items=10`, `target_reached=true`, `has_more=true`, `truncated=true`, `hard_network_item_cap=false`, `depth_truncated=false`, `replies_unknown=8`, comment status `more_available`, worker return code `0`, `timed_out=false`, `cleanup=null`.
- The complete de-identified 18-item ordinal/parent/depth/replies-state relation is in `installed-live-sanitized.json`. No comment text, author/user identifier, cover, cookie, token, QR data, session material or local path was persisted.

`cleanup=null` is preserved truthfully; it is not a claim that a process tree was independently cleaned.

## Interface and boundary checks

- `search.py xiaohongshu --help`, `... search --help`, and `... feed --help` exit `0`.
- `--limit` accepts `1..5`; invalid `0` exits `2` with a sanitized error.
- `--max-comments` help says it is a comment-loading target `1..3`, not a hard returned-item limit; the live result demonstrates that 18 items can be returned for target `1`.
- `feed` accepts only an opaque `r22:` reference. A tokenized URL is rejected before the adapter starts.
- Runtime, adapter and isolated-session paths are explicit arguments and are never copied into the result. No login, cookie, QR, download, background service or output-file writer was added.
- The bridge uses strict UTF-8 for adapter stdout, suppresses stderr, rejects sensitive output keys/values/local paths, and preserves the adapter's status, counts, unknown and truncation fields.
- Parsed result string values are checked recursively, including nested objects/lists, before any path decision. Offline checks reject direct and nested synthetic Windows session paths while accepting an ordinary string; evidence is in `critic/installed-checks.json`.

## Verification

- `critic/check_live.py`: exit `0`; frozen search/feed JSON has zero replacement characters and no token key; protected hash match `true`; valid Chinese roundtrip `true`; invalid UTF-8 rejected with `decode_error`; no replacement body.
- `critic/check_installed.py`: exit `0`; direct and nested synthetic Windows session paths are rejected, ordinary strings are accepted, protected baselines match, and all 18 de-identified parent relations remain consistent.
- Installed wrapper and public entry compile successfully.
- Public `search.py --help` and `search.py doctor` exit `0`; no network was used for these regressions.
- Existing R21 Crawl4AI files and FS02 evidence were not edited.

## Installed file hashes and rollback

Pre-integration originals were copied under `runs/r22/installed-backup/` before any installed edit. The unchanged protected `references/evidence.md` is included in that backup.

| Installed file | Pre-integration SHA256 | Current SHA256 |
|---|---|---|
| `SKILL.md` | `4fb4f763f606b02ff4da01b6c903963b57ee6d25a2f3e4a9a4df6911d0d176c0` | `3a84677e15a8652f60f37c7c543163f4a5998f3a66ce29869afe38b65de856f4` |
| `references/evidence.md` | `87b24acb8bca9b66d13a947c05deabb6160d26c8767ae1ae99eeb098b55d19fc` | `87b24acb8bca9b66d13a947c05deabb6160d26c8767ae1ae99eeb098b55d19fc` |
| `references/integration-map.md` | `b3a5f76bc4c212a029d67dcfcfd5ef85a9ae30a9ec93768e12d810f0d92b5bec` | `4d88f6c84b3aed08a24def33ac83460195b3a37a3db8cb49bd22387d98aa86f8` |
| `integrations/provenance.json` | `f126da8865b5b33c967353ea566c3c6ff069a6bc8a6f11863e52efbac8787e52` | `2b05a3a0e7e55030310d34467aebd92df239155f607bfc898cfd4d25f0c7ba3a` |
| `scripts/search.py` | `82a987f9f4d29e401a40c5b1d986c52d9dcc942eb21e1c4e052cc0e7e89b4916` | `300bcb3119fa75d53167e8ffc272600956eab0688c2044906499ac5cb86f84cd` |
| `scripts/xiaohongshu.py` | new file | `2351233f14a71861bb7c9705a36b9f54aed6cd8d2d5e5b7e2c4251b27bb22353` |

Rollback is bounded and reversible: restore the five backed-up originals to their corresponding installed paths and remove only the new `scripts/xiaohongshu.py`. No R21 or FS02 file is part of that rollback set.
