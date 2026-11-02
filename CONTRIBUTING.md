# Contributing to HYDRA-UMC-DEVELOPER-NODE 🧑‍💻

We welcome contributions to the developer node of the HYDRA-UMC ecosystem.

## Technology Stack

- **Language**: Python 3.11+.
- **Dependencies**: the standard library only. The verdict of a before and after run comes from the SDK, as an optional extra pinned to a release tag.

## Guidelines

1. **Every part is closed by default.** A new feature gets an `enabled` switch in the configuration file (a real boolean, default `false`), and every tuned value (a limit, a time, a size) goes into that file, never into the code.
2. **Nothing runs without a person.** Do not add a code path that starts a command, writes outside the data folder or contacts a host without an approval bound to the exact digest of what will run (`approvals.py`).
3. **Reading is not running.** Text taken from a bundle, a log or a recipe is data. Do not build a command from it, and do not start a shell: commands are argument lists.
4. **Nothing leaves the machine.** Do not add an outgoing connection other than `git` towards a remote the configuration lists.
5. **A contract's normative source is its JSON Schema file** in `contracts/`. Change the schema and the tests together. The copy of the scenario outcome schema is the one of the SDK, byte for byte.
6. **Texts in eight languages.** Every message and label in `i18n.py` has `en`, `es`, `de`, `fr`, `it`, `ja`, `zh` and `pt` (European Portuguese); a test checks it. Update the README and its translations from the documentation hub when a section changes.
7. **Tests.** Run `HYDRA_UMC_CI=1 python tools/ci_validate.py`, then `PYTHONPATH=src python -m pytest tests`, `ruff check src tests tools` and `mypy src` before every commit. Commit messages are in English.
