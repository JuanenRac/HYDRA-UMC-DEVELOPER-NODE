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
| `plugin list` / `plan` / `approve` / `run` | The `ecosystem-ci` plugin: show the plan and its digest, approve it (at a terminal), run it. |

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
