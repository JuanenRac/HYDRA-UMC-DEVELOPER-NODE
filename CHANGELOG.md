# Changelog

All notable changes to this project are documented here.

## [Unreleased]

## [0.0.2] - A full mode of the ecosystem CI plugin that runs the heavy tests of every repository after one approval of the whole batch, one repository at a time, with limits of time, output and free disk, and a consolidated report

- **Complete mode of the `ecosystem-ci` plugin, closed by default:** besides the shared CI, it can run the heavy test a repository declares in its manifest (`developer_node.full_test`); a repository that declares nothing runs nothing. The plan lists every command repository by repository with the SHA-256 of each script, and a person approves the whole batch by its digest (it expires and is used up by the run) after leaving out the repositories they do not want.
- **Serial and bounded runs:** one command at a time, a time limit per command and in total, a limit on the output size, a minimal environment without anything that looks like a secret, offline hints unless the repository declares that it needs the network and the configuration allows it, and nothing outside the approved list is ever started.
- **Disk protection:** the complete mode refuses to start, and stops between commands, when the disk of the workspace has less free space than `ecosystemCiFull.minFreeGb` (10 GB by default).
- **Clean cancellation and a consolidated report:** Ctrl+C ends only the processes the run started and still writes the report (`pass`, `fail`, `timeout`, `skipped` per command, with the duration and a short redacted tail); the exit code is not 0 when anything failed, timed out or was cut short.
- **New commands and settings:** `plugin full-plan`, `full-approve` and `full-run` (each with `--exclude`), the `ecosystemCiFull` section of the configuration file, the `ecosystem-ci-full-report/1` contract and `last_ci_full_report` in the status document, with the new texts in eight languages.

## [0.0.1] - The first pieces of the developer node: evidence intake, repro cases, a cache of checkouts, a status document and the ecosystem-ci plugin, all closed by default

- **Evidence intake, closed by default:** `evidence verify` checks a bundle of the local technician without storing it; `evidence ingest` also accepts a signed `incident-transport/1` message (HMAC-SHA256, receiver, age, nonce kept against replay) and stores a verified bundle as a case that waits for a person. A bundle that was edited after assembly or that carries a secret shape is refused; nothing in it is ever run.
- **Executable repro cases, closed by default:** a recipe (a list of argument lists and one condition) runs only when the part is on, every program is in the allow-list of the configuration and a person approved its exact digest at a terminal (expiring, single use). Each run is a `ScenarioOutcome` of the SDK contract; the verdict of a before and after pair is computed by the SDK (optional `sdk` extra, pinned to a tag).
- **Checkout cache by revision, closed by default:** a bare mirror per allowed remote and one detached git worktree per commit, a pinned commit is verified, and the cache keeps to a limit in GB set in the configuration by removing the least recently used worktrees.
- **Status document for dashboards and studios:** `developer-node-status/1` with the switches, the queue, the journal and the health, in eight languages, written to a file (no port, no command channel).
- **`ecosystem-ci` plugin, closed by default:** the shared CI validator of each repository of a workspace, one after another, after a person approved the exact plan, with one consolidated report.
- One JSON configuration file for every switch and every tuned value; texts of the command line and the panel in eight languages.
