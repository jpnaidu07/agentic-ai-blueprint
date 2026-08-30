"""Create local development secrets once. Never print tokens or overwrite configuration."""

import hashlib
import json
import os
import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    env = root / ".env"
    if env.exists():
        print("Existing .env preserved; manage identities and rotation explicitly.")
        return
    identities, credentials = [], []
    for role in ("admin", "evaluator", "reviewer", "viewer"):
        token = secrets.token_urlsafe(32)
        identities.append(
            {
                "user_id": f"local-{role}",
                "role": role,
                "tender_ids": ["*"],
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            }
        )
        credentials.append(f"{role}: {token}")
    config = (root / ".env.example").read_text(encoding="utf-8")
    config = config.replace(
        "AUTH_USERS=[]", "AUTH_USERS='" + json.dumps(identities, separators=(",", ":")) + "'"
    )
    config = config.replace(
        "POSTGRES_PASSWORD=\n", "POSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n"
    )
    credential_file = root / ".local-credentials.txt"
    if credential_file.exists():
        raise SystemExit(
            "Existing credentials file found without .env; resolve it manually to avoid accidental rotation"
        )
    for path, content in [
        (
            credential_file,
            "Synthetic-data development only. These roles have all-tender access.\n"
            + "\n".join(credentials)
            + "\n",
        ),
        (env, config),
    ]:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    print(
        "Created .env and .local-credentials.txt; both are ignored by git. Use only synthetic data."
    )
    if os.name == "nt":
        print(
            "Windows: ensure these files inherit access only for your user; use an encrypted local disk."
        )


if __name__ == "__main__":
    main()
