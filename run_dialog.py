import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4


MODES = {
    "main": ("Quality first: usually higher bitrate, larger file", ["--main"]),
    "high": ("Size first: usually lower bitrate, smaller file", ["--high"]),
    "audio": ("Audio only", ["--ns", "--nv", "--keep"]),
    "subtitles": ("Subtitles only", ["--nv", "--na", "--keep"]),
}
QUALITY_FLAGS = {
    "video_main": "--main", "video_high": "--high", "video_main480": "--main480",
    "hevc": "--hevc", "hdr": "--hdr", "novideo": "--nv", "noaudio": "--na",
    "nosubs": "--ns", "keep": "--keep",
}
TITLE = re.compile(
    r"(?:[0-9]+|https?://(?:www\.)?netflix\.com/"
    r"(?:\w+/)?(?:title|watch)/[0-9]+(?:[/?#].*)?)"
)
SELECTION = re.compile(r"[1-9][0-9]*(?:-[1-9][0-9]*)?(?:,\s*[1-9][0-9]*(?:-[1-9][0-9]*)?)*")
RETRY_FILE = Path(__file__).resolve().with_name(".download-retry.json")


def load_retry():
    try:
        saved = json.loads(RETRY_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(saved, dict):
        return None
    title, seasons, episodes = (saved.get(key) for key in ("title", "seasons", "episodes"))
    if (
        isinstance(title, str) and re.fullmatch(r"[0-9]+", title)
        and isinstance(seasons, str) and re.fullmatch(r"[0-9]+(?:,[0-9]+)*", seasons)
        and isinstance(episodes, str) and re.fullmatch(r"[0-9,~ -]*", episodes)
    ):
        flags = saved.get("quality_flags")
        resolution = saved.get("resolution")
        if not isinstance(flags, list) or any(flag not in QUALITY_FLAGS.values() for flag in flags):
            saved.pop("quality_flags", None)
        if not isinstance(resolution, str) or not re.fullmatch(r"[0-9]+", resolution):
            saved.pop("resolution", None)
        return saved
    return None


def save_retry(title, seasons, episodes, args):
    saved = {
        "title": str(title),
        "seasons": ",".join(map(str, seasons)),
        "episodes": episodes or "",
        "quality_flags": [flag for field, flag in QUALITY_FLAGS.items() if getattr(args, field, False)],
        "attempt": uuid4().hex,
    }
    if args.customquality and re.fullmatch(r"[0-9]+", args.customquality[0]):
        saved["resolution"] = args.customquality[0]
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=RETRY_FILE.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            json.dump(saved, file)
            file.close()
            temporary.replace(RETRY_FILE)
        finally:
            temporary.unlink(missing_ok=True)
    return saved


def clear_retry(saved):
    if saved and load_retry() == saved:
        RETRY_FILE.unlink(missing_ok=True)


class Cancelled(Exception):
    pass


def dialog(*args):
    result = subprocess.run(
        ["dialog", "--output-fd", "1", "--title", "Netflix-DL", *args],
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, "DIALOG_ERROR": "2"},
    )
    if result.returncode in (1, 255):
        raise Cancelled
    if result.returncode:
        sys.exit("Could not open the terminal dialog. Check your TERM setting or pass ARGS explicitly.")
    return result.stdout.strip()


def ask(prompt, pattern, error, *, optional=False):
    while True:
        value = dialog("--inputbox", prompt, "0", "0")
        if (optional and not value) or pattern.fullmatch(value):
            return value
        dialog("--msgbox", error, "0", "0")


def select_seasons(video):
    choices = []
    for season in video.get("seasons") or []:
        number = str(season["seq"])
        count = len(season.get("episodes") or [])
        label = f"Season {number} ({count} {'episode' if count == 1 else 'episodes'})"
        choices.extend([number, label, "off"])
    if not choices:
        sys.exit("Netflix returned no seasons for this title.")

    while True:
        selected = dialog(
            "--separate-output", "--checklist",
            "Choose seasons. Press Space to select and Enter to continue.",
            "0", "0", "0", *choices,
        )
        if selected:
            return [int(number) for number in selected.splitlines()]
        dialog("--msgbox", "Select at least one season to continue.", "0", "0")


def select_episodes():
    return ask(
        "Enter episodes such as 1-3,5. Leave blank for all episodes in the selected seasons.",
        SELECTION,
        "Use episode numbers or ranges such as 1-3,5.",
        optional=True,
    )


def main():
    if not shutil.which("dialog") or not sys.stdin.isatty() or not sys.stderr.isatty():
        sys.exit(
            "Interactive setup needs dialog and a terminal. On macOS install it "
            "with brew install dialog. You can also pass ARGS explicitly."
        )

    root = Path(__file__).resolve().parent
    cookies = root / "configs" / "Cookies"
    if not any((cookies / name).is_file() for name in ("cookies.txt", "cookies_nf.txt")):
        message = (
            "1. In Chrome, install Get cookies.txt LOCALLY by kairi003 "
            "from the Chrome Web Store. The link appears below this dialog.\n"
            "2. Sign in at netflix.com and keep the Netflix tab active.\n"
            "3. Click Chrome's Extensions puzzle-piece icon and select "
            "Get cookies.txt LOCALLY.\n"
            "4. Set Export format to Netscape and click Export for the current tab.\n"
            "5. Save the export to Downloads and run make cookies-copy.\n"
            "6. Run make run again. Keep the cookie file private."
        )
        store_url = (
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/"
            "cclelndahbckbenkjhflpdbgdldlbecc"
        )
        dialog("--cr-wrap", "--msgbox", message, "0", "70")
        sys.exit(f"{message}\n\nChrome Web Store\n{store_url}")

    saved = load_retry()
    if saved:
        episodes = saved["episodes"] or "All"
        flags = saved.get("quality_flags")
        quality = "Not saved"
        if flags is not None:
            quality = next(
                (name.title() for name, (_, options) in MODES.items() if set(options) == set(flags)),
                None,
            )
            quality = quality or (" ".join(flags) if flags else "Default")
        if saved.get("resolution"):
            quality += f" ({saved['resolution']}p)"
        choice = dialog(
            "--cr-wrap", "--menu",
            f"Previous download did not finish.\nTitle ID: {saved['title']}\n"
            f"Seasons: {saved['seasons']}\nEpisodes: {episodes}\nQuality: {quality}",
            "14", "64", "2", "reuse", "Reuse these selections", "new", "Choose new selections",
        )
        if choice == "new":
            saved = None
    title = saved["title"] if saved else ask(
        "Enter a Netflix title ID or title/watch URL.", TITLE, "Enter a numeric ID or a Netflix title/watch URL."
    )
    flags = saved.get("quality_flags") if saved else None
    if flags is None:
        choices = [item for name, (label, _) in MODES.items() for item in (name, label)]
        mode = dialog(
            "--menu",
            "What do you want to download? Main and High both include audio and subtitles. "
            "Picture quality depends on the title and the streams Netflix offers.",
            "0", "0", "0", *choices,
        )
        flags = MODES[mode][1]
    args = [title, *flags, "--interactive-selection"]
    if saved:
        if saved.get("resolution"):
            args.extend(["-q", saved["resolution"]])
        args.extend(["-s", saved["seasons"]])
        if saved["episodes"]:
            args.extend(["-e", saved["episodes"]])
    os.execv(sys.executable, [sys.executable, str(root / "NFripper.py"), *args])


if __name__ == "__main__":
    try:
        main()
    except Cancelled:
        pass
