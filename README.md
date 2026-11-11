## Docker Desktop

### Windows

Start Docker Desktop in Linux containers mode. Open PowerShell in the project
folder and build the image:

```powershell
docker compose build
docker compose run --rm netflix-dl --help
```

Export your signed-in Netflix cookies in Netscape format and save the export as
`configs/Cookies/cookies.txt`. Run the interactive dialog or pass the usual CLI
arguments:

```powershell
docker compose run --rm netflix-dl
docker compose run --rm netflix-dl 80014749 --high
```

### macOS

Start Docker Desktop and run the same commands from Terminal in the project
folder. On Apple Silicon, the image runs as `linux/amd64` because the bundled
Windows helper is x86-64. In Docker Desktop settings, select the Apple
Virtualization framework and enable Rosetta for amd64 emulation.
[Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/)

### Files and diagnostics

Downloads appear in `downloads/netflix` on the host. If you pass `-o` or `-f`,
use a container path under `/app/downloads` to keep the files on the host.
Compose also keeps cookies, tokens, cached keys, and dialog retry selections
across runs. If prompted for fallback credentials, the app saves them to
`.docker-state/.env`. You can copy an existing app `.env` there before running.

To test the bundled Wine helper with local fixtures:

```sh
docker compose run --rm netflix-dl wine-check
```

## Native installation

1. Install python 3.10.7 (or any version from 3.8.x to 3.10.x), be sure to add python to PATH while installing it

https://www.python.org/ftp/python/3.10.7/python-3.10.7-amd64.exe

https://datatofish.com/add-python-to-windows-path/

2. Install Visual C++ Redistributable Packages for Visual Studio 2013

https://www.microsoft.com/en-eg/download/details.aspx?id=40784

3. Run install.requirements.bat

   If you have GNU Make, `make build` creates a local `.venv` and installs
   `requirements.txt`. After completing the cookie setup below, `make run`
   opens a terminal dialog for the title and download mode. For series, it
   fetches the available seasons and lets you select one or more before
   entering an optional episode range. Install `dialog` first if needed (`brew install dialog`
   on macOS). To bypass the dialog, pass `ARGS` explicitly. Use
   `make run ARGS="--help"` to see the options, or pass a title and flags with
   `make run ARGS="80014749 --high"`. On macOS and Linux, Make looks for Python
   3.8–3.10 automatically. You can also set `PYTHON` to an executable path when
   creating the environment.

   On macOS, install the native media tools and then run `make run`.

   ```sh
   brew install aria2 bento4 ffmpeg media-info mkvtoolnix
   ```

   For protected video that needs a new license, the bundled `wv_cvt.exe`
   helper also needs a compatible `wine` executable on `PATH`. Run
   `make wine-check` to test the helper with the bundled fixtures. Audio and
   subtitle downloads can use the native tools without Wine. Windows uses
   the bundled executables.

   If Netflix rejects the bundled client with `DEVICE_EOL_FINAL` (3078),
   you can try a compatible Chrome Widevine device you already have
   provisioned. Point the app at its directory with this command.

   ```sh
   NETFLIX_LICENSE_DEVICE_DIR="/absolute/path/to/device" make run
   ```

   The directory must contain `device_private_key` and
   `device_client_id_blob`. If it contains `device_vmp_blob`, the app
   includes it in the request. Keep these files outside the checkout.
   This mode uses the existing Python Widevine code without Wine.
   Netflix must accept the configured device before video processing can
   continue.

4. Manifest requests use the signed-in session when both `NetflixId` and
   `SecureNetflixId` are available. If either cookie is missing, the app uses
   email and password. `make run` prompts for missing credentials, hides password input, and saves the answers to
   the Git-ignored `.env` file. You can also fill in `.env.sample` and save
   it as `.env`, or supply `NETFLIX_EMAIL` and `NETFLIX_PASSWORD` as
   environment variables. Environment variables take precedence over
   `.env`, followed by credentials in `configs/config.py`.

5. Install this Chrome extension

   After exporting Netflix cookies in Netscape format to `~/Downloads`, run
   `make cookies-copy` to copy the newest valid Netflix export into the app's
   cookie folder. Then run `make run`. Use `make cookies-remove` to clear the
   app's imported and cached cookies.

https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid

and go to netflix.com and download the cookies, rename the file to cookies.txt and put it in

configs\Cookies

For Firefox use this addon

https://addons.mozilla.org/en-US/firefox/addon/cookies-txt-one-click/

6. In the script's folder three batches

**A download.video.bat**

For downloading the video in AVC high profile with the audio and subtitles use

`python NFripper.py --high`

For downloading the video in Main profile with the audio and subtitles use

`python NFripper.py --main`

the script will download only the original audio with the highest bitrate and all the available subtitles, 
to download the audio in all the available languages use

`python NFripper.py --high --all-audios`

or

`python NFripper.py --main --all-audios`

To set the default audio language in config.py replace

`"AUDIO": "None",`

with the language you want, for example for the French language to be the default audio language use

`"AUDIO": "fra",`

To set the default subtitles language in config.py replace

`"SUB": "None",`

with the language you want, for example for the English language to be the default subtitles language use

`"SUB": "eng",`

If you want to downlod the video for a specific seasons or all the seasons use

`python NFripper.py 80014749 --high -s 1`

`python NFripper.py 80014749 --high -s 1,3,5`

`python NFripper.py 80014749 --high -s 1-5`

To download the video in 720p use

`python NFripper.py --high -q 720`

If you do not want to download the subtitles use

`python NFripper.py --high --ns`

When you run any of the three batches you will be asked for the URL of the TV Show or the movie in Netflix

for example use this link to download the video of Rick and Morty

https://www.netflix.com/title/80014749

or you could add the ID like this

`python NFripper.py 80014749 --high`

The downloads will be saved in the folder `"downloads\netflix"`

For adding more options use the instructions in NFripper.py, open the file with Notepad++.

**B. download.subtitles.bat**

For downloading only the subtitles

`python NFripper.py --nv --na --keep --slang eng`

change eng to the language you need to download the subtitles in.

To download the subtitles in multiple languages use

`python NFripper.py --nv --na --keep --slang eng fra rus pol`

If you want to downlod the subtitles for a specific episode or episodes use

`python NFripper.py --nv --na --keep --slang eng -s 1 -e 8`

`python NFripper.py --nv --na --keep --slang eng -s 1 -e 1-3`

`python NFripper.py --nv --na --keep --slang eng -s 1 -e 2,4,7`

You could download the subtitles of all the seasons by using

`python NFripper.py 70153404 --nv --na --keep -s 1-10 --slang eng`

remove --slang eng if you want to download the subtitles in all of the available languages in Netflix of your country.

To download the subtitles in all of the languages and all the forced subtitles use

`python NFripper.py --nv --na --keep --all-forced`

To download the forced subtitles in specific languages use

`python NFripper.py --nv --na --keep --flang jpn tha`

**C. download.audio.bat**

For downloading only the audio

`python NFripper.py --ns --nv --keep --alang eng`

change eng to the language you need to download the audio in

To download the audio in multiple languages use

`python NFripper.py --ns --nv --keep --alang eng fra rus pol`

To download the audio in 2 channels only use

`python NFripper.py --ns --nv --keep --only-2ch-audio`

To download the audio in AAC codec use

`python NFripper.py 80014749 --ns --nv --keep --alang eng -s 1 -e 1 --aformat-51ch aac`

*or*

`python NFripper.py 80014749 --ns --nv --keep --alang eng -s 1 -e 1 --aformat-2ch aac`

To download the audio in a specific bitrate use

`python NFripper.py 81185548 --audio-bitrate 384`

If the metadata request returns an empty response, compare the title ID in the
error with the URL in your browser. If Netflix rejects the session with HTTP 401,
export fresh cookies from the signed-in Netflix tab and run `make cookies-copy`.

**Don't put any files in the folder configs\Tokens, the script will generate netflix_token.json by itself.**

In case of getting any error messages with aria2c you could disable it by adding the command `--no-aria2c`

`python NFripper.py --no-aria2c --high`

**To download the Interactive TV shows and movies, in MSLClient.py which is in the folder helpers/Parsers/Netflix/ 
change it to "isBranching": True and after you download the video change it to "isBranching": False.**

https://help.netflix.com/en/node/62526


