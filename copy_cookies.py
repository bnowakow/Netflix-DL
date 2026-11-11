import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time


def read_netflix_export(path):
    cookies = {}
    now = time()
    with open(path, encoding="utf-8-sig") as export:
        if not export.readline().startswith(("# Netscape HTTP Cookie File", "# HTTP Cookie File")):
            raise ValueError("Expected a Netscape cookie export")
        for line in export:
            if line.startswith("#HttpOnly_"):
                line = line[len("#HttpOnly_"):]
            elif not line.strip() or line.startswith("#"):
                continue
            domain, _, _, _, expiry, name, value = line.rstrip("\r\n").split("\t")
            domain = domain.lstrip(".").lower()
            if domain != "netflix.com" and not domain.endswith(".netflix.com"):
                raise ValueError("Export contains cookies for other sites")
            if not expiry or int(expiry) == 0 or int(expiry) > now:
                cookies[name] = value
    return cookies


def find_export(downloads):
    candidates = sorted(
        (path for path in downloads.glob("*.txt") if path.is_file()),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    for path in candidates:
        try:
            cookies = read_netflix_export(path)
        except (OSError, ValueError):
            continue
        if cookies.get("NetflixId"):
            return path
    return None


def copy_export(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        path = Path(temporary.name)
        try:
            with source.open("rb") as export:
                shutil.copyfileobj(export, temporary)
            temporary.close()
            path.replace(destination)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    source = find_export(Path.home() / "Downloads")
    if source is None:
        raise SystemExit(
            "No valid Netflix cookie export found in ~/Downloads. In Chrome, "
            "open the signed-in Netflix tab, select Netscape, and click Export."
        )

    destination = Path(__file__).resolve().parent / "configs/Cookies/cookies.txt"
    copy_export(source, destination)
    print(f"Copied {source.name} to configs/Cookies/cookies.txt. Run make run next.")
