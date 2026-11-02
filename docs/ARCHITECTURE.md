<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - docs/ARCHITECTURE.md
Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

# Architecture

The developer node is the place where a failure found on a node of the ecosystem is studied: it receives the evidence, gets the exact source of the revision involved, reproduces the failure with a fixed recipe and, only when a person says so, runs the shared CI over a workspace. It never changes a repository and never sends anything out of the machine.

## The parts

| Part | Module | What it does |
|---|---|---|
| Configuration | `settings.py` | One JSON file. Every part has an `enabled` switch that must be a real boolean and is closed by default; every tuned value lives in the file. |
| Evidence intake | `evidence.py` | Reads a bundle of `HYDRA-UMC-LOCAL-TECHNICIAN` (a file, or a signed `incident-transport/1` message). Checks the signature, the receiver, the age, the nonce, the shape, the checksum and the absence of secrets, then stores a case that waits for a person. Read only: the bundle is never changed and nothing it says is run. |
| Repro recipes | `repro.py`, `approvals.py` | A recipe is a list of argument lists and one condition. It runs only when the part is on, every command is allowed by the configuration and a person approved the exact digest of the recipe for that case. Each run is a `ScenarioOutcome` (the SDK contract); the verdict of a before and after pair is computed by the SDK. |
| Checkout cache | `checkouts.py` | A bare mirror per remote and one detached git worktree per commit, with a limit in GB set in the configuration; the least recently used worktrees go first. |
| Panel contract | `panel.py` | The status document (switches, queue, journal, health) that a dashboard or a studio shows. A file; there is no port and no command channel. |
| Plugin `ecosystem-ci` | `plugin_ci.py` | Runs `tools/ci_validate.py` of each repository of a workspace, one after another, after a person approved the exact plan, and writes one consolidated report. |
| Store | `store.py` | One SQLite file: cases, an append-only journal, approvals, run outcomes and the nonces already seen. |

## The flow of one incident

1. `evidence ingest` stores the bundle as a case (`awaiting-review`).
2. A person reviews it and writes a recipe; `checkout fetch` gets the exact revision.
3. `repro approve` (a person at a terminal types the start of the recipe's digest), then `repro run --phase before`.
4. After a candidate fix: `repro approve` again and `repro run --phase after` on the new revision.
5. `repro compare` gives the verdict from the SDK; an "apparent success" (the failure stopped but the source did not move) is never reported as fixed.

## Where it stops

The node does not apply a fix, does not push, does not talk to the network by itself (the only network access is `git` towards remotes the configuration lists) and does not expose a service. The panel is a contract only: the dashboard and the studio read the document, and this repository does not edit them.
