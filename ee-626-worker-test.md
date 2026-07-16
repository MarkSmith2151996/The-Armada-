# EE-626 Worker CDP Fix And Smoke Test

Generated: 2026-07-14

## Worker Spec

Updated `~/.config/opencode/agents/brand-outreach-worker.md` in the Available Tools section.

The specification now requires workers to use the `cdp_port` assigned in their instruction directly with `browse_page` and explicitly prohibits `acquire_cdp` and `release_cdp`. Those names appear only in the prohibition, not as worker actions.

## CDP Cleanup

- Terminated four stale `armada-foreman` OpenCode processes: `51599`, `51695`, `51699`, and `51702`.
- Preserved the interactive OpenCode process and laptop-bridge SSH process.
- No process held any `/tmp/armada-cdp-pool/*.lock` file.
- Removed obsolete lock-file entries for ports `9226`-`9231`.
- Retained normal pool lock-file paths for `9222`-`9225`; these are file-lock targets, not active locks.
- Acquired all four pool ports (`9222`, `9223`, `9224`, `9225`) and released them successfully. The pool ended with four free ports and zero acquired ports.

## Bounded Smoke Test

Result: **FAILED - test control flow was not honored.**

A fresh OpenCode invocation was instructed to run `AI-86525`, dispatch only `AI-83473`, then stop. It exceeded the command time window and the foreman recorded that it dispatched 16 workers in two batches. Its recorded execution note reported CDP/step-limit issues and incomplete artifact writes.

- `AI-83473` has no local `node.db` session or tool result.
- The 16 initially assigned worker instructions remain `open` with no execution notes.
- No evidence was produced that a worker called `browse_page` with `cdp_port=9222`, used Serper, or completed a verdict.
- `AI-86525` was reset to `open` after the failed smoke session; no foreman is running.

## Next Required Action

Do not launch the four foremen yet. First make the foreman smoke-test harness enforce a one-worker limit independently of the foreman prompt, then retry the test. Restart active OpenCode sessions before normal launch so they load the revised worker agent specification.
