# Security Policy 🔒 (HYDRA-UMC-DEVELOPER-NODE)

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.x.x   | ✅ Yes    |

## Reporting a Vulnerability

**CRITICAL: Do not report vulnerabilities through public GitHub issues.**

This project is built around one limit: nothing runs without a person's approval of the exact thing that will run, every part is closed until the configuration file opens it, and nothing leaves the machine. If you find a vulnerability affecting:

- **Approvals** (`approvals.py`, `repro.py`, `plugin_ci.py`) - any way to start a command without an approval bound to its digest, to reuse or extend an approval, or to approve without a person at a terminal.
- **Evidence intake** (`evidence.py`) - any way to store a bundle that is forged, replayed, edited after assembly or that carries a secret, or any way text of a bundle can become a command.
- **The checkout cache** (`checkouts.py`) - any way to fetch from a remote that is not listed, to make git run a program, to write or remove outside the cache folder, or to check out a commit other than the one named.
- **Command execution** - any way to run a program that is not in `repro.allowedCommands`, to start a shell, to leave the checkout folder or to receive secrets from the environment.
- **Secret redaction** (`redaction.py`) - a real secret shape that is not masked in the output of a run or in an error message.
- **The configuration file** (`settings.py`) - a value that switches a part on without being a real `true`.

Please report responsibly:

1. **Email**: Send a detailed report to `electrohobby3d@gmail.com`.
2. **Impact**: Describe the attack surface affected and a realistic scenario.
3. **Response**: Initial acknowledgment within 48 hours.

We follow a coordinated disclosure policy.
