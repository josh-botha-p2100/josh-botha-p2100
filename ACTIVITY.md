# How the activity map works

The map combines three sources without treating them as the same kind of work.

| Colour | Source | Count |
|---|---|---|
| Ink | GitHub | Contributions reported by GitHub's contribution calendar |
| Project2100 blue | Claude | Recorded user prompts in available local Claude Code transcripts, with CLI history filling days where transcripts are absent |
| Light blue | Codex | Recorded user prompts in available local Codex sessions and archives |

Each column is one calendar day. The colours form separate layers. Height uses a logarithmic scale within each source, so a busy AI day does not hide GitHub activity. These counts do not measure tokens, time worked, code quality or productivity.

Desktop shows the latest 53 calendar weeks; the mobile layout shows 26 weeks with totals for that shorter range. Each layout's totals are summed from the exact days shown. GitHub supplies its own calendar dates. Local AI timestamps are converted to Australia/Sydney, including daylight saving.

## Coverage and refresh

GitHub refreshes daily through this repository's Actions workflow. Claude and Codex are a dated snapshot from local history, not account-wide analytics and not a live feed. Conversations used on other devices, in web apps, or no longer retained on this computer may be missing. Earlier dates with no retained history are unknown, rather than reconstructed as activity.

The snapshot records its coverage and refresh time in [data/ai-activity.json](data/ai-activity.json). Known subagents, guardian reviews, imported Claude threads, tool results, system events, compacted summaries and duplicated historical messages are excluded. CLI history supplements only dates without transcript prompts. A local cache of event hashes makes subsequent refreshes faster; that cache is ignored by Git.

## Refresh the local snapshot

From this repository on the computer holding the histories:

```sh
python -m pip install tzdata
python scripts/export-ai-activity.py
node scripts/update-stats.mjs
```

The Node script uses an existing GitHub CLI login locally, or `GITHUB_TOKEN` in Actions. Review the updated aggregate JSON and SVGs, then commit and push those files. The exporter itself never pushes. No local scheduled task has been installed.

Only daily counts, source coverage, timezone and snapshot time are published. Prompt text, session IDs, workspace paths, raw logs and credentials stay local. The parser checks can be run with `python scripts/test-activity.py`.
