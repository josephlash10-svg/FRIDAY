# Security policy

## Reporting a vulnerability

Please report security problems **privately**, not in a public issue:
**[Report a vulnerability](https://github.com/josephlash10-svg/friday-emotional-ai/security/advisories/new)** (GitHub's private vulnerability reporting).

Include what you found, how to reproduce it, and what an attacker could do with it. I'll aim to acknowledge reports within a week and keep you updated while a fix is made. Credit is given in the release notes unless you'd rather not be named.

## Supported versions

Only the latest release and `main` get security fixes. Friday is a single-maintainer research prototype.

## What's in scope

Friday runs entirely on your own computer, so most of its security is about what that local setup protects:

- **Checkpoints are pickle files.** `.pth` checkpoints are loaded with Python's pickle, which can run code. Only load the checkpoint shipped in this repository (`release/friday-base.pth`) or ones you created. Any way to make Friday load a checkpoint the user didn't choose is in scope.
- **The local language server.** Friday starts `llama-server` on `127.0.0.1` with a random key generated at every start. A way for a web page, another program, or another machine to use that server or read conversation content through it is in scope.
- **Your memories.** Conversations are stored in `state/`, which stays on your machine and is excluded from the repository. Anything that sends that data elsewhere, or leaks it into logs or files that are meant to be shared, is in scope.
- **Downloads.** `scripts/download_models.py` checks every model file and the llama.cpp build against pinned SHA-256 hashes and refuses to install anything that doesn't match. A way around those checks is in scope.

## What isn't a security issue

**Unsafe or harmful replies**, such as missing a safety check or downplaying abuse, are bugs we take seriously, but they belong in a regular issue with the `safety` label or a [Breaking persona](https://github.com/josephlash10-svg/friday-emotional-ai/issues/new?template=persona.md) issue, so the fix and the test can be public. If your report includes someone's real personal details or a real crisis conversation, send it privately through the link above instead.

Friday is not a crisis service. If you're in crisis, contact local emergency services, or in the US call or text **988**.
