# Final release report

Status: **PENDING LIVE GITHUB REHEARSAL**

This checked-in file is intentionally not presented as completed evidence.
After the repository is public and the first immutable release is published,
run `.github/workflows/final-rehearsal.yml`. The workflow generates a separate
`FINAL_RELEASE_REPORT.md` from live GitHub API data and uploads it together with
`portfolio-evidence.json` and the recovery report.

Completion requires public links for all of the following:

- source repository and exact release commit;
- successful unified release workflow;
- immutable GitHub Release and its assets;
- GHCR image pinned by SHA-256 digest;
- successful `Security gate` on the tag commit;
- successful clean-room final rehearsal workflow.

See `docs/PUBLICATION_RUNBOOK.md` for the exact execution and acceptance steps.
