<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - docs/CONFIGURATION.md
Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

# Configuration

`configs/developer-node.json` is the whole configuration, and it ships with everything closed. Pass it with `--config`. Without a file every switch is closed. A key the node does not know is an error, and a switch that is not a real JSON boolean (the text `"true"`, the number 1) is an error, never a way to switch something on.

| Section | Key | Default | Meaning |
|---|---|---|---|
| (top) | `dataDir` | `developer-node-data` | Where the database, the mirrors, the worktrees and the reports live. |
| (top) | `language` | `en` | One of `en es de fr it ja zh pt` (European Portuguese). |
| `ingest` | `enabled` | `false` | Allows `evidence ingest`. |
| | `maxBundleBytes` | 1000000 | A bigger file is refused. |
| | `requireTransportMac` | `true` | A bare bundle (without a signed message) is refused. |
| | `secretEnv` / `secretFile` | `HYDRA_UMC_DEVELOPER_NODE_TRANSPORT_SECRET` / empty | Where the shared secret is read from (at least 24 characters); never from the command line. |
| | `expectedToNode` | `developer-node` | The receiver name a message must carry. |
| | `maxClockSkewSeconds` / `nonceRetentionSeconds` | 300 / 86400 | The age window and how long a nonce is remembered. |
| `repro` | `enabled` | `false` | Allows `repro run`. |
| | `allowedCommands` | `[]` | Names of the programs a recipe may start; empty allows nothing. |
| | `approvalMaxAgeMinutes` | 30 | An approval expires and is single use. |
| | `stepTimeoutSeconds` / `maxSteps` / `maxOutputBytes` | 60 / 20 / 65536 | Bounds of a run. |
| `checkouts` | `enabled` | `false` | Allows the cache of checkouts. |
| | `allowedRemotes` | `[]` | A remote is fetched only when it is one of these or lies below one. |
| | `maxCacheGb` | 5.0 | The cache limit; the least recently used worktrees are removed to fit it. |
| | `mirrorsDir` / `worktreesDir` / `gitTimeoutSeconds` | `mirrors` / `worktrees` / 120 | Folders (inside `dataDir`) and the time limit of git. |
| `panel` | `enabled` | `false` | Allows `panel status` and `panel export`. |
| | `maxJournalEntries` | 200 | Entries of the journal in the status document. |
| `ecosystemCi` | `enabled` | `false` | Allows the plugin. |
| | `workspace` / `repos` | empty | The folder with the repositories and the names of those to check. |
| | `timeoutSeconds` / `tailLines` / `approvalMaxAgeMinutes` | 600 / 12 / 30 | Time limit per repository, lines kept of each output, approval life. |
| `ecosystemCiFull` | `enabled` | `false` | Allows the complete mode (it also needs `ecosystemCi.enabled`; it uses its `workspace` and `repos`). |
| | `perRepoTimeoutSeconds` / `totalTimeoutSeconds` | 1800 / 7200 | Time limit of each command and of the whole batch. |
| | `maxOutputBytes` | 1000000 | A command that writes more is stopped and counted as failed. |
| | `minFreeGb` | 10.0 | The run is refused, or stops, when the disk of the workspace has less free space. |
| | `allowNetwork` | `false` | A repository that declares `needs_network` is skipped unless this is true. |
| | `includeCiValidate` / `manifestFile` | `true` / `hydra-umc.project.json` | Run the shared CI too; the manifest that declares the heavy test. |
| | `passEnv` | `[]` | Extra names of environment variables to pass (names that look like secrets are never passed). |
| | `tailLines` / `approvalMaxAgeMinutes` | 15 / 30 | Lines kept of each output, approval life. |
