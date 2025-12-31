from __future__ import annotations

import os
from pathlib import Path


def load_secrets_file(path: Path = Path(".secrets")) -> dict[str, str]:
    secrets: dict[str, str] = {}
    if not path.exists():
        return secrets

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if key in os.environ:
            continue
        os.environ[key] = value
        secrets[key] = value
    return secrets
