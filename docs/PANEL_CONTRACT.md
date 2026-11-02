<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - docs/PANEL_CONTRACT.md
Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

# The status document for dashboards and studios

`hydra-umc-developer-node panel export` writes `<dataDir>/panel/status.json` (a temporary file and a rename, so a reader never sees half of it); `panel status` prints the same document. The shape is the contract `developer-node-status/1`, in `contracts/panel_status.schema.json`.

| Field | Meaning |
|---|---|
| `contract`, `version`, `language`, `generated_at` | The contract name, the node version, the language of `labels` and the time of the document. |
| `switches` | The state of each part (`ingest`, `repro`, `checkouts`, `panel`, `ecosystemCi`, `ecosystemCiFull`). |
| `queue` | Cases by status, approvals not used yet, recorded runs. |
| `journal` | The latest entries (id, time, kind, case, a short detail), newest first. |
| `health` | Database integrity, size of the checkout cache against its limit, summary of the last ecosystem CI report and of the last complete one (`last_ci_full_report`). |
| `labels` | The texts of the panel in the language of the document (eight languages are available). |

The document holds counts, kinds and short details only: never a bundle, a recipe or the output of a command. It has no command channel: a dashboard shows it and cannot change the node through it. How the file reaches a dashboard (an authenticated tunnel, a copy) is decided by the dashboard's side; the node opens no port.
