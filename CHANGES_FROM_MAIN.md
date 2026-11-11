# Changes from local main

Baseline: local `main` at `7f498722d5c915ddac39b25276d266c0ea1ead5c` (`first commit`). Reviewed on 2026-11-11 against HEAD `c0b798e2dc9ff32fb517d55802f2ef2f117117c1` and the working tree.

This report describes the net tracked changes from `git diff main`, including committed, staged, and unstaged work, plus the untracked project skill. It excludes this report, generated downloads, local state, and secret values. No remote comparison is involved.

## Setup and commands

- [Makefile](Makefile) adds `make build` to create `.venv` and install dependencies, with a requirements installation marker so unchanged requirements are not reinstalled on every run. On macOS/Linux it searches for Python 3.8–3.10; `PYTHON` and `VENV` can override defaults. Windows defaults to `python` and the Windows virtual environment layout.
- `make run` builds first and opens the terminal dialog. Supplying `ARGS` explicitly invokes the existing CLI instead, for example `make run ARGS="--help"` or `make run ARGS="80014749 --high"`.
- [requirements.txt](requirements.txt) adds `six`; other listed dependencies remain as before.
- [README.md](README.md) documents Make setup, dialog operation, native macOS dependencies, Wine requirements, credential precedence, cookie import/removal, and revised metadata troubleshooting. It replaces instructions to put account credentials directly in configuration.

For the documented macOS setup:

```sh
brew install dialog
brew install aria2 bento4 ffmpeg media-info mkvtoolnix
make build
make cookies-copy
make run
```

Export signed-in Netflix cookies in Netscape format to `~/Downloads` before `make cookies-copy`. The Make automation also uses shell utilities; the existing Windows batch entry points remain available.

## Cookie import and authentication

- [copy_cookies.py](copy_cookies.py) scans `~/Downloads/*.txt`, newest modification time first, for a valid Netflix-only Netscape export containing a usable `NetflixId`. It supports HTTP-only cookie lines and UTF-8 BOMs, discards expired cookies when parsing, rejects other-site cookies, and atomically copies the chosen export to `configs/Cookies/cookies.txt`. Validation does not require `SecureNetflixId`, so successful import alone does not guarantee cookie-based manifest authentication.
- [services/netflix.py](services/netflix.py) prefers an existing text export over the cached cookie/build data, validates it with the shared parser, and reports missing, invalid, or unusable exports explicitly. `make cookies-remove` in [Makefile](Makefile) removes both `configs/Cookies/cookies.txt` and `configs/Cookies/cookies_nf.txt`.
- [netflix_credentials.py](netflix_credentials.py) resolves each credential from a nonempty environment variable, then `.env`, then the legacy configuration value, ignoring the original placeholders. Missing credentials are prompted for in a terminal and saved atomically to `.env`; password entry must be hidden. Noninteractive missing credentials and invalid quoted `.env` values produce explicit failures. The file parser supports plain, single-quoted, and JSON double-quoted credential values rather than a general dotenv syntax.
- [.env.sample](.env.sample) declares `NETFLIX_EMAIL` and `NETFLIX_PASSWORD`. [.gitignore](.gitignore) excludes `.env`, `.venv`, retry state, imported/cached cookies, generated tokens, and Python bytecode caches. Saved credentials and cookies remain sensitive local files.
- [helpers/Parsers/Netflix/MSLClient.py](helpers/Parsers/Netflix/MSLClient.py) uses `NETFLIXID` authentication when both `NetflixId` and `SecureNetflixId` are supplied; otherwise it resolves email/password credentials. Cookie mode selects the browser manifest router and supplies cookie, browser/build, handshake, and manifest payload parameters. It rejects unsuccessful HTTP and empty manifest responses, gives a specific email/password rejection message, and logs structured manifest rejection codes without dumping the full error object.
- [helpers/Parsers/Netflix/get_manifest.py](helpers/Parsers/Netflix/get_manifest.py) accepts cookies/build and passes them to the MSL client. [helpers/Parsers/Netflix/get_keys.py](helpers/Parsers/Netflix/get_keys.py) does the same for key requests, including the HEVC fallback; [services/netflix.py](services/netflix.py) supplies the active session to both paths.

## Interactive selection and retry behavior

- [run_dialog.py](run_dialog.py) adds a `dialog` interface that requires a terminal and the `dialog` executable. It validates numeric title IDs and Netflix title/watch URLs, offers Main, High, audio-only, and subtitle-only modes, and shows cookie setup instructions when neither cookie file exists. Main/High descriptions explain the usual bitrate/size tradeoff without guaranteeing stream quality.
- [services/netflix.py](services/netflix.py) loads available series seasons for the interactive checklist and accepts an optional episode list/range. Existing CLI season/episode selections still work. Direct episode IDs retain their season and episode for retry; a selection matching no episodes now fails explicitly.
- [run_dialog.py](run_dialog.py) atomically saves series selections in `.download-retry.json`: title, seasons, episodes, supported quality/mode flags, numeric resolution when present, and an attempt identifier. A subsequent dialog run can reuse them or choose new selections. Saved mode labels are matched by the complete flag set, and saved resolution is validated before reuse. Invalid saved data is ignored or its invalid quality fields are discarded.
- [services/netflix.py](services/netflix.py) saves retries before processing series downloads, except check/license modes, and clears a matching retry record only when every selected item reports completion. Declined downloads or failures retain it; the attempt identifier prevents clearing a replacement record from a different attempt. This records selections rather than transfer progress, covers series rather than movies, and does not preserve every CLI option, such as language/proxy settings.
- [NFripper.py](NFripper.py) adds the hidden `--interactive-selection` switch and handles dialog cancellation with a successful exit. The dialog runner also treats cancellation as a normal exit.

## Metadata diagnostics and output failures

- [services/netflix.py](services/netflix.py) uses the `release` metadata endpoint, sets a 30-second request timeout, and retries HTTP 502/503/504 up to three total attempts with one- and two-second delays. Connection errors, HTTP 401, other HTTP failures, empty responses, and malformed/missing video metadata receive distinct messages with the title ID. Empty responses no longer assert regional unavailability, and parsing failures no longer automatically delete cached cookies.
- The same file checks video-processing success and whether a returned mux output path exists before cleanup. It stops with an explicit error on these failures, allowing series retry selections to remain available.

## macOS media tools

- [configs/config.py](configs/config.py) selects native commands from `PATH` on Darwin for Bento4, FFmpeg/FFprobe, MediaInfo, mkvmerge, and aria2c; other platforms keep the existing binary map.
- [services/netflix.py](services/netflix.py) checks the macOS tools required by the selected video/audio mode before downloading and provides the Homebrew install command when tools are missing. A failed macOS video decryption returns failure before demuxing.
- [helpers/ripprocess.py](helpers/ripprocess.py) places `--key` options before input/output paths on macOS for native `mp4decrypt`, retaining the prior ordering elsewhere.
- [helpers/Parsers/Netflix/get_keys.py](helpers/Parsers/Netflix/get_keys.py) requires a compatible `wine` on macOS for the bundled `wv_cvt.exe` license helper. Challenge/response conversion runs in temporary directories with subprocess failure handling and automatic cleanup. The existing Windows helper path remains. Native audio/subtitle workflows do not require this Wine conversion, but protected video needing a new license still does; native tool selection does not remove that limitation.

## Developer workflows and documentation skill

- [utilities/codex-commit.sh](utilities/codex-commit.sh) operates on already staged changes, locates the selected agent CLI, optionally uses an installed commit-message skill, generates a message, and creates the commit. It then fetches upstream state, offers a rebase with autostash if behind, and prompts to push, inspect the last commit diff, or cancel. Agent-assisted conflict resolution edits conflicted files; the script checks markers, stages those paths, and continues the rebase. Only transient transport timeouts trigger network retries, up to three attempts. These commands can modify Git history/index and contact remotes when explicitly run; they are not part of report generation.
- [utilities/claude-commit.sh](utilities/claude-commit.sh) selects Claude for the shared commit flow. The shared script supports CLI overrides through `CODEX_BIN`/`CLAUDE_BIN`, dialog/whiptail interfaces with plain prompt fallback, and an offered Claude login/retry on authentication failure. [Makefile](Makefile) exposes both workflows as `make codex-commit` and `make claude-commit`.
- `make github-sync` requires a clean working tree, fetches `origin` and `upstream`, fast-forwards local `main` through both main refs, merges main into `bnowakow`, and atomically pushes both branches to origin. It assumes those remotes/branches exist and stops on failures or conflicts; it is a repository-specific synchronization command.
- The untracked [skills/netflix-dl-document-changes/SKILL.md](skills/netflix-dl-document-changes/SKILL.md) defines this local-main comparison, complete project-file coverage, secret/generated-file exclusions, and a report-only editing scope. `make install-skills` copies repository skills into `${CODEX_HOME:-$HOME/.codex}/skills`, replacing matching files. `make codex-document` invokes the Codex CLI with workspace-write sandboxing to refresh this report; `CODEX` overrides that executable.

## Review scope and validation

Coverage was checked against all 17 tracked paths differing from local `main` and the one untracked project skill. Generated subtitle downloads were excluded without reading their contents. Credential files, cookie exports, and local retry state were not opened. This is a source/diff review; it does not establish successful Netflix authentication, media downloads, Wine compatibility, or remote Git operations. Only `CHANGES_FROM_MAIN.md` was edited for this task; the Git index and refs were left untouched.
