import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


MODES = {
    "main": ("Quality first: usually higher bitrate, larger file", ["--main"]),
    "high": ("Size first: usually lower bitrate, smaller file", ["--high"]),
    "audio": ("Audio only", ["--ns", "--nv", "--keep"]),
    "subtitles": ("Subtitles only", ["--nv", "--na", "--keep"]),
}
TITLE = re.compile(
    r"(?:[0-9]+|https?://(?:www\.)?netflix\.com/"
    r"(?:\w+/)?(?:title|watch)/[0-9]+(?:[/?#].*)?)"
)
SELECTION = re.compile(r"[1-9][0-9]*(?:-[1-9][0-9]*)?(?:,\s*[1-9][0-9]*(?:-[1-9][0-9]*)?)*")


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
            "5. Save the export to Downloads and run make copy-cookies.\n"
            "6. Run make run again. Keep the cookie file private."
        )
        store_url = (
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/"
            "cclelndahbckbenkjhflpdbgdldlbecc"
        )
        dialog("--cr-wrap", "--msgbox", message, "0", "70")
        sys.exit(f"{message}\n\nChrome Web Store\n{store_url}")

    title = ask("Enter a Netflix title ID or title/watch URL.", TITLE, "Enter a numeric ID or a Netflix title/watch URL.")
    choices = [item for name, (label, _) in MODES.items() for item in (name, label)]
    mode = dialog(
        "--menu",
        "What do you want to download? Main and High both include audio and subtitles. "
        "Picture quality depends on the title and the streams Netflix offers.",
        "0", "0", "0", *choices,
    )
    args = [title, *MODES[mode][1], "--interactive-selection"]
    os.execv(sys.executable, [sys.executable, str(root / "NFripper.py"), *args])


if __name__ == "__main__":
    try:
        main()
    except Cancelled:
        pass
