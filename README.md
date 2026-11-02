<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - Developer node: evidence, repro cases and checkouts, approved by a person
Copyright (C) JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

<p align="center">
  <img src="images/HYDRA_UMC_BANNER.svg" alt="HYDRA-UMC-DEVELOPER-NODE banner" width="100%">
</p>

# 🧑‍💻 HYDRA-UMC-DEVELOPER-NODE

<p align="center">🇺🇸 <b>English</b> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 🧑‍💻 Developer Node: Studies Failures, Reproduces Them, Runs Nothing Unapproved

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="Core">
  <img src="https://img.shields.io/badge/Parts-closed%20by%20default-367BF5.svg" alt="Parts">
  <img src="https://img.shields.io/badge/Tests-70%20passing-2ea44f.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-0.0.1-0f6cbd.svg" alt="Version">
  <img src="https://img.shields.io/badge/Maturity-scaffolding-FFB020.svg" alt="Maturity">
</p>

---

**Honesty check - what actually runs today:** the evidence intake (signature, nonce, checksum, secret check), the executable repro cases with approvals bound to a digest, the checkout cache with its limit, the status document, the `ecosystem-ci` plugin and the eight-language texts are real and tested (70 automated tests, run with local git repositories and local processes). The node has not run on a real development host, a recipe is not isolated beyond an allow-list and a minimal environment, and nothing takes work from the queue by itself. See `CHANGELOG.md` for exactly what has shipped.

---

> **Safety and security status:** this ecosystem is not a certified safety system. There is no hardware E-STOP path, no firmware-enforced limits or interlocks and no verified motion command yet; firmware images are checked with CRC-32 and an Ed25519 signature, and a release build refuses the published development keys (the tool heads and expansion boards behind the relay still run URTC bootloaders, which take a shared-key HMAC-SHA256 instead of a signature); TLS and mutual TLS are optional and off by default; no custom board has been populated or tested yet. Read the [security baseline](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md) and the [threat model](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md) before relying on any statement here for the safety of a person.

---

## 📋 At a glance

| | |
|---|---|
| Version | `0.0.1` |
| Maturity | Scaffolding |
| Tests | 70 (`python -m pytest -q tests`) |
| Stack | Python 3.11+ / JSON Schema / SQLite / git worktree |
| Target | A development server |
| On real hardware | Not applicable: nothing here runs on hardware |

**Jump to:** [Overview](#-overview) · [Architecture](#-architecture) · [Quick start](#-quick-start) · [Testing](#-testing) · [Repository Structure](#-repository-structure) · [Related Projects](#-related-projects)

## 🚦 Project status

Each line is one part of this repository and the light says how far it is today. It is written from what the repository can show (tests, builds, runs), not from what is planned.

🟢 Done and verified · 🟡 Works, with known limits · 🟠 Partly done or not verified yet · 🔴 Not done or not working

| Area | State | What it means here |
|---|---|---|
| Software | 🟠 | Structure and first pieces only; most of the work is still to do |
| Tests | 🟡 | 70 automated tests, run on every change |
| Real hardware | 🟡 | Not applicable: nothing here runs on hardware |
| Interface and protocols | 🟡 | The routes or messages it offers are documented and tested with a client; not every client has used them yet |
| Integration | 🟡 | Its messages and routes are checked against the shared contracts of the SDK; it has not run together with the real equipment |
| Security | 🟡 | Access control, input limits or signatures are implemented and tested on a computer; nobody outside the project has reviewed them |
| Operation | 🟠 | It writes logs; it has no metrics or health endpoint yet |
| Documentation | 🟡 | README in eight languages, checked against the manifest on every change |

## 🎯 Overview

HYDRA-UMC-DEVELOPER-NODE is the developer node of the ecosystem: the place where a failure that a node has reported is studied. It reads the evidence bundle of `HYDRA-UMC-LOCAL-TECHNICIAN` (read only), gets the exact source of the revision involved from a cache of git worktrees, reproduces the failure with a fixed recipe and can run the shared CI over a workspace.

Four rules hold everywhere. Every part is **closed** until the configuration file opens it. Nothing runs without **a person approving the exact thing that will run**. Nothing **leaves the machine**. Every tuned value lives in the **configuration file**, never in the code.

This version ships five independent pieces:

1. **Evidence intake** (`evidence.py`) - checks a bundle or a signed `incident-transport/1` message (signature, receiver, age, nonce, shape, checksum, no secrets) and stores it as a case that waits for a person.
2. **Executable repro cases** (`repro.py`, `approvals.py`) - a recipe of argument lists, allowed commands only, an approval bound to its digest; each run is a `ScenarioOutcome` of the SDK and the SDK gives the verdict of a before and after pair.
3. **Checkout cache by revision** (`checkouts.py`) - a bare mirror and one git worktree per commit, a pinned commit verified, a limit in GB kept by removing the least recently used worktrees.
4. **Status document** (`panel.py`) - queue, journal and health for a dashboard or a studio, in eight languages, as a file.
5. **`ecosystem-ci` plugin** (`plugin_ci.py`) - the shared CI validator of each repository of a workspace, with one consolidated report. In the complete mode (closed by default) it can also run the heavy test each repository declares, as one batch a person approves by its digest, one repository at a time, with limits of time, output and free disk.

## 🧩 Role in HYDRA-UMC

**HYDRA-UMC-DEVELOPER-NODE** is the developer node of the ecosystem: it reads the evidence bundles of `HYDRA-UMC-LOCAL-TECHNICIAN`, keeps a cache of checkouts by revision, runs repro recipes and the shared CI, and each of these stays closed until the configuration opens it and a person approves the exact run.

## 🏛️ Architecture

<p align="center">
  <img src="images/architecture.svg" alt="HYDRA-UMC-DEVELOPER-NODE architecture" width="100%">
</p>

## 🚀 Quick start

Requires Python 3.11 or newer.

```bash
./build.sh  # Linux, macOS (build.bat on Windows)
./run.sh
./run.sh --config configs/developer-node.json evidence verify bundle.json
```

## 🧪 Testing

70 automated tests run with `python -m pytest -q tests`. They need no hardware and nothing outside this machine.

The CI runs `HYDRA_UMC_CI=1 python tools/ci_validate.py`, which checks the manifest, the documents, the eight READMEs and the pictures.

## 🏗️ Build & Release

```bash
chmod +x build.sh   # one-time
./build.sh          # creates .venv, pip install -e ".[dev]", compile-checks + tests
./run.sh            # checks the shipped configuration (every switch closed)
./run.sh --config configs/developer-node.json evidence verify bundle.json
./run.sh --version
```

On Windows: `build.bat`, then `run.bat`. `test.sh` / `test.bat` run the tests and the checks without changing the version. The verdict of a before and after pair needs the SDK: `pip install -e ".[dev,sdk]"`.

**Troubleshooting**

- `Refused: ... is closed`: the part is off. Open it in the configuration file (`"enabled": true`, a real boolean) and read [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- `no valid approval for this exact recipe`: approve the recipe again with `repro approve`; an approval expires and works once.
- `an approval needs a person at a terminal`: run the approval in a terminal, not from a script or a pipe.

## 📂 Repository Structure

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of HYDRA-UMC-DEVELOPER-NODE" width="100%">
</p>

<details>
<summary>Text version of the tree</summary>

```text
HYDRA-UMC-DEVELOPER-NODE/
├── src/hydra_umc_developer_node/   source code
│   ├── cli.py                      command line
│   ├── settings.py                 configuration and switches
│   ├── evidence.py                 evidence bundle checks and intake
│   ├── repro.py                    repro recipes and runs
│   ├── checkouts.py                checkout cache by revision
│   ├── panel.py                    status document for dashboards
│   ├── plugin_ci.py                ecosystem-ci plugin
│   ├── plugin_full.py              complete mode of the ecosystem-ci plugin
│   ├── approvals.py                approval by a person
│   ├── store.py                    local database and journal
│   ├── schema.py                   contract checker
│   ├── redaction.py                secret redaction
│   └── i18n.py                     texts in eight languages
├── contracts/                      JSON Schema contracts
├── tests/                          automated tests
├── configs/                        example configuration, all closed
├── docs/                           documents of the project
├── tools/                          project tools and CI checks
├── images/                         Media and app icons
├── .github/                        CI workflow and issue templates
├── build.sh / build.bat            venv + editable install + compile-check + tests
├── run.sh / run.bat                Forwards a real CLI command
├── bump_version.py                 explicit version bump
├── bump_manifest_version.py        Syncs hydra-umc.project.json's version to the native one (--sync)
├── CHANGELOG.md                    what changed in each version
├── build-test.sh                   non-mutating build check
├── hydra-umc.project.json          manifest: version, maturity, family
├── pyproject.toml                  package metadata
└── test.sh                         runs the tests
```

</details>

## 🗺️ Roadmap & Known limits

**Known limits today**

This version ships the five pieces above. What is not here yet:

- **Isolation of a run.** A recipe runs with the rights of the user who runs the node, with an allow-list of programs, a minimal environment and time and output limits; there is no sandbox (container, namespaces) around it yet. A person must read a recipe before approving it.
- **A stronger approval.** An approval is a record in the local database made at a terminal; it is not signed with a key of the approver.
- **The panel on the other side.** The status document is a contract and a file; `HYDRA-UMC-DASHBOARD-AI` and `HYDRA-UMC-STUDIO` do not show it yet, and how the file reaches them (an authenticated tunnel) is theirs to decide.
- **A worker loop.** Cases, recipes and checkouts are used by commands; nothing takes a case from the queue and works it by itself, on purpose.
- **A run on a real development host.** The node has been tested on a computer with local git repositories only.

## 🌍 Languages

This README and the documents of the repository exist in eight languages: English, Spanish, German, French, Italian, Japanese, Chinese and Portuguese (Portugal). They are written together and checked in the CI so that the eight files have the same sections and the same links. This repository has no screen or message catalogue of its own, so there are no interface strings to translate.

## 🔗 Related Projects

This project is part of the HYDRA-UMC robotics ecosystem by the same author (JuanenRac / Electro Hobby 3D). Worth knowing about, since a request might actually be about one of these rather than this repository.

**Directly Related**
- **[HYDRA-UMC-LOCAL-TECHNICIAN](https://github.com/JuanenRac/HYDRA-UMC-LOCAL-TECHNICIAN)** — produces the evidence bundles this node reads; the node only checks and stores them, it never changes them or runs what they say.
- **[HYDRA-UMC-DEV-SERVER](https://github.com/JuanenRac/HYDRA-UMC-DEV-SERVER)** — reproducible development host with a durable task queue; this node is the lighter place where one failure is studied and reproduced after a person approves each run.
- **[HYDRA-UMC-OPS-AGENT](https://github.com/JuanenRac/HYDRA-UMC-OPS-AGENT)** — owns the maintenance-incident lifecycle (evidence, diagnosis, human-approved change, canary deploy, verification); this node supplies the reproduction step and never approves a change.
- **[HYDRA-UMC-SDK](https://github.com/JuanenRac/HYDRA-UMC-SDK)** — the shared contracts: the scenario outcome of every repro run follows its schema, and the SDK computes the verdict of a before and after pair.

**Also Part of the Ecosystem**

*Core Hardware & Platform*
- **[HYDRA-UMC](https://github.com/JuanenRac/HYDRA-UMC)** — the robot-arm motherboard design: CM5 host + dual-core STM32H745, meant to orchestrate up to 8 tool arms over CAN-OTA/SPI-OTA (firmware at an early stage; no populated board yet).
- **[HYDRA-UMC-OS](https://github.com/JuanenRac/HYDRA-UMC-OS)** — reproducible Raspberry Pi OS product layer for the CM5: read-only agent, validated config/profiles, WiFi first-contact provisioning.

*Core Backend & Clients*
- **[HYDRA-UMC-SERVER](https://github.com/JuanenRac/HYDRA-UMC-SERVER)** — the real headless backend (REST/WebSocket) every control client actually talks to.
- **[HYDRA-UMC-STUDIO](https://github.com/JuanenRac/HYDRA-UMC-STUDIO)** — web control dashboard with real-time multi-robot 3D visualization.
- **[HYDRA-UMC-SUITE](https://github.com/JuanenRac/HYDRA-UMC-SUITE)** — desktop (PySide6) swarm command center for multiple servers at once.
- **[HYDRA-UMC-ANDROID-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-ANDROID-CONTROL)** — native Android control app with biometric login and a paired Wear OS companion.
- **[HYDRA-UMC-IOS-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-IOS-CONTROL)** — iOS/iPadOS control app (Flutter) with real-time WebSocket sync.
- **[HYDRA-UMC-DSI](https://github.com/JuanenRac/HYDRA-UMC-DSI)** — native touch UI for the onboard 7" DSI touchscreen, embedded on the CM5 itself.
- **[HYDRA-UMC-EDITOR-URDF](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-URDF)** — desktop graphical URDF creator/editor that pushes finished models into STUDIO's own catalog.
- **[HYDRA-UMC-EDITOR-STL](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-STL)** — desktop STL model editor, transforming/replacing/removing/adding real parts in the same model catalog HYDRA-UMC-EDITOR-URDF also edits.
- **[HYDRA-UMC-BRIDGE-AMR](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-AMR)** — coordination boundary for AGV/AMR fleets via a VDA 5050 MQTT publisher (tested against an emulated fleet only).
- **[HYDRA-UMC-BRIDGE-CNC](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-CNC)** — high-level CNC-cell coordinator with GRBL status/control-byte access (tested against an emulator only).
- **[HYDRA-UMC-BRIDGE-DROIDS](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-DROIDS)** — coordination boundary for legged/humanoid droids, with a Boston Dynamics Spot command sender (tested against an emulator only).
- **[HYDRA-UMC-BRIDGE-LASER](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-LASER)** — laser-cell coordinator reading 3 key/enclosure/interlock GPIO signals (tested against a fake chip only; it cannot arm or fire a laser).
- **[HYDRA-UMC-BRIDGE-OPENPNP](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-OPENPNP)** — safe high-level board-flow coordinator for OpenPnP pick-and-place.
- **[HYDRA-UMC-BRIDGE-PRINTER3D](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-PRINTER3D)** — safe coordination boundary for Moonraker/Klipper 3D printers, with real gated job commands.
- **[HYDRA-UMC-BRIDGE-ROS2](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-ROS2)** — coordinator with a lazily imported rclpy ROS 2 transport (not yet run against a ROS 2 installation).
- **[HYDRA-UMC-BRIDGE-UAV](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-UAV)** — coordination boundary for camera-equipped UAVs, with a MAVLink command sender (tested against an emulator only).

*URTC Tool Platform*
- **[URTC](https://github.com/JuanenRac/URTC)** — firmware for the physical Universal Robot Tool Controller PCB, 25+ tool profiles over CAN bus.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — desktop GUI flashing tool for URTC boards, CAN-OTA plus full-chip SWD/JTAG.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — desktop live CAN-bus diagnostic tool for URTC boards, one panel per tool profile.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — browser-based alternative to URTC-TESTER via the Web Serial API, no local install needed.
- **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** — gateway in front of the URTC CAN bus: an allowed list of identifiers, a rate limit and a session key; software tested on a computer, not yet on a real bus.

*Vision AI Node (Hailo-8)*
- **[HYDRA-UMC-VISION-NODE](https://github.com/JuanenRac/HYDRA-UMC-VISION-NODE)** — integration hub for the Hailo-8 vision pipeline, with a real per-stage hardware-readiness check.
- **[HYDRA-UMC-DETECTION-HEF](https://github.com/JuanenRac/HYDRA-UMC-DETECTION-HEF)** — real compiled-model registry with Hailo-architecture/checksum safe-load verification.
- **[HYDRA-UMC-VISION-STREAMER](https://github.com/JuanenRac/HYDRA-UMC-VISION-STREAMER)** — real GStreamer pipeline + MediaMTX config generator with a real HailoRT integration boundary.
- **[HYDRA-UMC-VISUAL-SERVOING-API](https://github.com/JuanenRac/HYDRA-UMC-VISUAL-SERVOING-API)** — Position-Based Visual Servoing correction law with authorisation gated on the zone state; no camera pose estimation yet.
- **[HYDRA-UMC-SAFETY-ZONES](https://github.com/JuanenRac/HYDRA-UMC-SAFETY-ZONES)** — v0 zone-breach, calibration-freshness and E-STOP-request logic that takes object positions from a file; no detector feeds it and no physical E-STOP is wired to it yet.

*Cognitive AI Node (Hailo-10)*
- **[HYDRA-UMC-COGNITIVE-NODE](https://github.com/JuanenRac/HYDRA-UMC-COGNITIVE-NODE)** — integration hub for the Hailo-10 cognitive pipeline (LLM/VLA/voice orchestration).
- **[HYDRA-UMC-VLA-ENGINE](https://github.com/JuanenRac/HYDRA-UMC-VLA-ENGINE)** — real action-token encoding/decoding and trajectory generation for a Vision-Language-Action model.
- **[HYDRA-UMC-VOICE-UI](https://github.com/JuanenRac/HYDRA-UMC-VOICE-UI)** — real voice front-end (VAD + intent parser) with a bounded, confirmation-gated Watch relay - it has no outbound-notification surface, so this project publishes its incident events to the broker of the ecosystem instead.
- **[HYDRA-UMC-SEMANTIC-PLANNER](https://github.com/JuanenRac/HYDRA-UMC-SEMANTIC-PLANNER)** — real rule-based task decomposition and semantic error recovery over MCU error codes.
- **[HYDRA-UMC-DOCS-QA](https://github.com/JuanenRac/HYDRA-UMC-DOCS-QA)** — real stdlib-only TF-IDF document search over this ecosystem's own Markdown docs.

*Orchestration & Swarm*
- **[HYDRA-UMC-ORCHESTRATOR](https://github.com/JuanenRac/HYDRA-UMC-ORCHESTRATOR)** — integration hub with a real gRPC/Protobuf health-report contract and mission state machine.
- **[HYDRA-UMC-JOB-DISPATCHER](https://github.com/JuanenRac/HYDRA-UMC-JOB-DISPATCHER)** — real priority-based job queue with deduplication, over a real HTTP API.
- **[HYDRA-UMC-PATH-PLANNER-3D](https://github.com/JuanenRac/HYDRA-UMC-PATH-PLANNER-3D)** — real RRT-based 3D path planner with real obstacle/workspace collision validation.
- **[HYDRA-UMC-SWARM-SYNC](https://github.com/JuanenRac/HYDRA-UMC-SWARM-SYNC)** — real CRDT LWW-Element-Map state sync, property-tested for multi-cell convergence.
- **[HYDRA-UMC-NODE-HEALING](https://github.com/JuanenRac/HYDRA-UMC-NODE-HEALING)** — a real gRPC-based fleet health watchdog with its own retry/backoff and identity-mismatch detection.

*Digital Twin & Simulation*
- **[HYDRA-UMC-TWIN](https://github.com/JuanenRac/HYDRA-UMC-TWIN)** — integration hub for the digital-twin engine, with a real version-compatibility sync contract.
- **[HYDRA-UMC-HIL-BRIDGE](https://github.com/JuanenRac/HYDRA-UMC-HIL-BRIDGE)** — hardware-in-the-loop router with a software collision interlock between simulation and real hardware (tested without real hardware).
- **[HYDRA-UMC-PHYSICS-REPLICA](https://github.com/JuanenRac/HYDRA-UMC-PHYSICS-REPLICA)** — real forward kinematics and joint-limit validation over a real URDF subset.
- **[HYDRA-UMC-SYNTHETIC-DATA-GEN](https://github.com/JuanenRac/HYDRA-UMC-SYNTHETIC-DATA-GEN)** — real procedural 2D scene generator with YOLO/COCO annotation export.

*Data & Analytics*
- **[HYDRA-UMC-DATALAKE](https://github.com/JuanenRac/HYDRA-UMC-DATALAKE)** — real sqlite3-backed time-series store with a real ingest/query HTTP API.
- **[HYDRA-UMC-ANOMALY-DETECTOR](https://github.com/JuanenRac/HYDRA-UMC-ANOMALY-DETECTOR)** — real FFT + statistical baseline anomaly detector with drift monitoring.
- **[HYDRA-UMC-PRODUCTION-REPORTS](https://github.com/JuanenRac/HYDRA-UMC-PRODUCTION-REPORTS)** — real OEE/availability calculation over DATALAKE history, with reproducible CSV export.
- **[HYDRA-UMC-TELEMETRY-COLLECTOR](https://github.com/JuanenRac/HYDRA-UMC-TELEMETRY-COLLECTOR)** — real CAN/WebSocket ingestion pipeline into DATALAKE, with sequence deduplication.

*Industrial Gateway*
- **[HYDRA-UMC-GATEWAY-INDUSTRIAL](https://github.com/JuanenRac/HYDRA-UMC-GATEWAY-INDUSTRIAL)** — integration hub relaying to industrial protocols, with a real command allowlist/backpressure layer.
- **[HYDRA-UMC-OPCUA-SERVER](https://github.com/JuanenRac/HYDRA-UMC-OPCUA-SERVER)** — real OPC-UA address space, verified with a real binary-protocol client session.
- **[HYDRA-UMC-MQTT-BROKER](https://github.com/JuanenRac/HYDRA-UMC-MQTT-BROKER)** — real MQTT broker with optional per-client authentication and topic ACLs.
- **[HYDRA-UMC-MTCONNECT-ADAPTER](https://github.com/JuanenRac/HYDRA-UMC-MTCONNECT-ADAPTER)** — real MTConnect `/probe` and `/current` XML endpoints with degraded-mode output.

*Complementary Tools*
- **[HYDRA-UMC-DASHBOARD-AI](https://github.com/JuanenRac/HYDRA-UMC-DASHBOARD-AI)** — Smart Summaries and Anomaly Highlighting panels over DATALAKE/ANOMALY-DETECTOR, with an honest statistical fallback.
- **[HYDRA-UMC-TOOL-CLI](https://github.com/JuanenRac/HYDRA-UMC-TOOL-CLI)** — fleet CLI with a real, stable exit-code contract, a genuine live client of HYDRA-UMC-SERVER's own API.
- **[HYDRA-UMC-WATCH](https://github.com/JuanenRac/HYDRA-UMC-WATCH)** — WearOS companion app with haptic alert patterns and a paired-phone voice relay (not yet run on a physical watch).
- **[HYDRA-UMC-CONNECTOR-HUB](https://github.com/JuanenRac/HYDRA-UMC-CONNECTOR-HUB)** — external adapter capability catalog, GET-only by design.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — firmware for a board-mounting rack with real tool-ID decoding and Smart Idle pre-heating logic.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — firmware plus a real Python vision companion for a thermal/RGB inspection tool head.
- **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** — administrative desktop tool that discovers, clones and updates every repo in this ecosystem.
- **[HYDRA-UMC-OS-REBUILDER](https://github.com/JuanenRac/HYDRA-UMC-OS-REBUILDER)** — builds a fresh CM5 image from source, another "Ecosystem Operations" sibling.

## 📚 Documentation

Where to read more:

* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — the parts, the flow of one incident and where the node stops.
* **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — every switch and every tuned value of the configuration file.
* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — every command, the exit codes and the shape of a recipe.
* **[docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)** — the rules the node keeps and what is not covered.
* **[docs/PANEL_CONTRACT.md](docs/PANEL_CONTRACT.md)** — the status document for dashboards and studios.
* [Security baseline of the ecosystem](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)
* [Threat model of the ecosystem](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)
* [Changelog of this repository](CHANGELOG.md)
* [License of this repository](LICENSE.md)

## 🤝 Contributing & Community

* Before a pull request run `HYDRA_UMC_CI=1 py -3 tools/ci_validate.py` (or `HYDRA_UMC_CI=1 python3 tools/ci_validate.py`): it must print `CI_VALIDATION=PASS`. Do not run `build.sh` or `build.bat` for this check; building is not a check.
* The eight READMEs are written from one source in HYDRA-UMC-DOCS; do not edit them by hand. Change the source and write them again with `tools/make_readmes.py`.
* Do not state in a README what has not run: say "simulated" or "not tried on hardware" where that is the truth.
* See [CONTRIBUTING.md](CONTRIBUTING.md), the [code of conduct](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md) and [SUPPORT.md](SUPPORT.md).

## 👤 AUTHOR

**JuanenRac (Electro Hobby 3D)** · electrohobby3d@gmail.com

## 📜 LICENSE

GPL-3.0-or-later - [LICENSE](LICENSE).
