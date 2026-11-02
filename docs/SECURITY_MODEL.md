<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - docs/SECURITY_MODEL.md
Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

# Security model

The rules the node keeps, each with the test that holds it.

1. **Everything is closed by default.** A part runs only when its `enabled` switch is a real boolean `true` in the configuration file.
2. **Nothing runs without a person.** A recipe or a CI plan runs only with an approval bound to its exact SHA-256 digest. The approval is made at a terminal, by typing the start of the digest just shown; input that is not a terminal creates nothing. It expires, and the first run uses it up. A recipe changed after approval needs a new approval.
3. **Reading a bundle runs nothing.** The text of a bundle is data. It is checked (shape, checksum, secrets) and stored; no field of it is ever turned into a command.
4. **A signed message is checked in a fixed order.** Signature first (HMAC-SHA256 over the canonical JSON, compared in constant time), then the contract, the receiver, the age, and only then the nonce is remembered, so a forged message cannot use up a real nonce.
5. **Commands are argument lists, never a shell string.** Only programs named in `repro.allowedCommands` start; the folder of a step must be relative and inside the checkout; the environment is minimal; time and output are bounded; the output is redacted before it is kept.
6. **Only listed remotes are fetched,** with a boundary at a slash, and git is started without prompts and with the `ext` transport off.
7. **The cache only removes what it made.** A worktree folder is removed only if it has the metadata file the node wrote and lies inside the cache; any other folder is left alone and reported.
8. **Nothing leaves the machine.** The node opens no port and sends nothing. Its only network use is `git` towards the listed remotes.
9. **Secrets are never printed.** The transport secret comes from a file or an environment variable and is not put in a message; error messages go through the redaction.
10. **The environment given to the plugin leaves out names that look like secrets.**

What is not covered: the programs an approved recipe starts have the rights of the user who runs the node; a person must read a recipe before approving it. Run the node as a user with no more rights than the work needs.
