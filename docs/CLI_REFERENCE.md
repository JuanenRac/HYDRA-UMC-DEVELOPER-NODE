<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - docs/CLI_REFERENCE.md
Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

# Command line reference

`hydra-umc-developer-node [--config FILE] [--lang CODE] <group> <command>`. Exit codes: 0 done, 1 refused (a closed switch, a missing approval, a failed check), 2 wrong usage.

| Command | What it does |
|---|---|
| `config check` / `config show` | Validate the configuration and list the closed switches / print the switches. |
| `evidence verify FILE` | Check a bundle (read only; stores nothing; needs no switch). |
| `evidence ingest FILE` | Check a bundle or a signed `incident-transport/1` message and store it as a case. Needs `ingest.enabled`. |
| `case list` / `case show ID` | List the cases / print one. |
| `repro check RECIPE` | Validate a recipe and print its digest. |
| `repro approve CASE RECIPE` | A person approves the digest for the case (needs a terminal). |
| `repro run CASE RECIPE --phase before\|after (--checkout NAME REMOTE REV \| --workdir DIR --fingerprint TEXT)` | Run an approved recipe; prints the `ScenarioOutcome`. |
| `repro compare CASE SCENARIO` | The verdict of the stored before and after runs, computed by the SDK (needs the `sdk` extra). |
| `checkout fetch NAME REMOTE REV` / `list` / `prune` | Make or reuse the worktree of a revision / list the cache / remove the least recently used worktrees until the cache fits its limit. |
| `panel status` / `panel export` | Print / write the status document. |
| `panel push` | Send the status document to HYDRA-UMC-SERVER with the token of this node (needs `serverPush.enabled`). |
| `plugin list` / `plan` / `approve` / `run` | The `ecosystem-ci` plugin: show the plan and its digest, approve it (at a terminal), run it. |
| `plugin full-plan [--exclude REPO]...` | The complete mode: print the plan (every command, repository by repository, with the SHA-256 of each script) and its digest. |
| `plugin full-approve [--exclude REPO]...` | A person approves the whole batch by its digest (needs a terminal; expires; single use). |
| `plugin full-run [--exclude REPO]...` | Run the approved batch one repository at a time and print the consolidated report. Exit code 1 if anything failed, timed out or the run was cut short. |

The complete mode runs `tools/ci_validate.py` of each repository and, only when the repository declares it, its heavy test. A repository declares it in its manifest:

```json
{"developer_node": {"full_test": {"interpreter": "python", "script": "tools/build_test.py", "needs_network": false}}}
```

`interpreter` is `python` or `sh`; `script` is a relative path inside the repository. A repository with no declaration runs only the shared CI (or nothing). Each repository can be left out with `--exclude`, before approval; the approval covers the exact list. Ctrl+C stops the command in progress (and the processes it started), leaves the rest as skipped and still writes the report.

Each result of the report is `pass`, `fail`, `timeout` or `skipped`, with the duration, an exit code and a short redacted tail of the output (`contracts/ecosystem_ci_full_report.schema.json`).

A recipe is a JSON document (`contracts/repro_recipe.schema.json`):

```json
{
  "schema_version": "1.0",
  "scenario_id": "server/health-endpoint",
  "repro_case": "health-returns-500",
  "steps": [{"argv": ["python", "-m", "pytest", "-q", "tests/test_health.py"]}],
  "reproduced_when": {"exit_code_not": 0}
}
```

The failure counts as reproduced when the last step ends with an exit code other than `exit_code_not`; earlier steps are preparation and must end with 0.
