import json
import os
import sys
import warnings
from getpass import GetPassWarning, getpass
from pathlib import Path
from tempfile import NamedTemporaryFile


ENV_PATH = Path(__file__).resolve().with_name(".env")
FIELDS = {
    "NETFLIX_EMAIL": ("email", "enter your email address here"),
    "NETFLIX_PASSWORD": ("password", "enter your password here"),
}


def save_credentials(path, lines, updates):
    existing = [line for line in lines if line.partition("=")[0].strip() not in updates]
    existing.extend(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in updates.items())
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write("\n".join(existing) + "\n")
            file.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def netflix_credentials(config):
    path = ENV_PATH
    try:
        lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    except FileNotFoundError:
        lines = []

    saved = {}
    for line in lines:
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if separator and key in FIELDS:
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except ValueError:
                    sys.exit(f"Invalid quoted value for {key} in .env.")
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            saved[key] = value

    credentials = {}
    updates = {}
    for key, (field, placeholder) in FIELDS.items():
        value = next(
            (value for value in (os.environ.get(key, ""), saved.get(key, ""), config[field])
             if value.strip() and value.strip() != placeholder),
            "",
        )
        if not value:
            if not sys.stdin.isatty():
                sys.exit(f"Missing {key}. Set it in .env or run make run in a terminal to enter it.")
            try:
                if field == "password":
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", GetPassWarning)
                        value = getpass("Netflix password: ")
                else:
                    value = input("Netflix email: ").strip()
            except GetPassWarning:
                sys.exit("Could not hide password input. Set NETFLIX_PASSWORD in .env and retry.")
            except (EOFError, KeyboardInterrupt):
                sys.exit("Netflix credential entry cancelled.")
            if not value.strip() or value.strip() == placeholder:
                sys.exit(f"Missing {key}. Run make run again to enter it.")
            updates[key] = value
        credentials[field] = value

    if updates:
        save_credentials(path, lines, updates)
        print("Saved Netflix credentials to .env.")
    return credentials["email"].strip(), credentials["password"]
