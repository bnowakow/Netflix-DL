# Netflix Widevine license error 3078

Netflix-DL reached the license step for *Doozie’s Doghouse*, season 1, episode 1 (series ID `81678020`). Netflix returned the manifest, and the video and audio tracks had already been downloaded. The license endpoint returned HTTP 200 with an application error in the response.

```text
Netflix rejected the bundled license client as end of life (DEVICE_EOL_FINAL, 3078).
```

The earlier HTTP 502 and this license rejection occurred on different attempts. The HTTP 200 response shows the request reached the endpoint, and `DEVICE_EOL_FINAL` identifies the rejection that currently blocks video decryption.

## macOS and Windows

Both bundled Wine fixtures passed on macOS. Those fixtures exercise the local helper. Netflix still rejected the bundled `chromecdm_2449` client during the live request. Netflix-DL uses that same bundled client by default on Windows.

Chrome on macOS uses `libwidevinecdm.dylib` for playback. An Apple Silicon copy was present in the local Chrome 157 installation. The browser's Encrypted Media Extensions API provides license sessions and exposes no raw credential export. No extraction method was verified for that installation. [Chromium Widevine component installer](https://chromium.googlesource.com/chromium/src/+/main/chrome/browser/component_updater/widevine_cdm_component_installer.cc) · [Encrypted Media Extensions specification](https://www.w3.org/TR/encrypted-media/)

A published Windows method extracted an RSA private key from Widevine `4.10.1610.0`. Its author reports that the method stopped working after the CDM was reworked. An export from current Windows Chrome and Netflix acceptance of the historical credentials were both unverified. [Windows extraction write-up](https://github.com/tomer8007/widevine-l3-decryptor/wiki/Reversing-the-old-Widevine-Content-Decryption-Module)

## Trying an existing device credential set

`NETFLIX_LICENSE_DEVICE_DIR` points to a directory containing the following files from a compatible Chrome Widevine device.

- `device_private_key`
- `device_client_id_blob`
- `device_vmp_blob` if available

If you already have a compatible `.wvd` file, put the standalone Pywidevine CLI
on PATH and run the export target. Use a destination outside the repository.
[Pywidevine export command source](https://github.com/devine-dl/pywidevine/blob/master/pywidevine/main.py#L1368)

```sh
NETFLIX_LICENSE_DEVICE_DIR="/absolute/path/to/exported-folder" make export-license-device WVD="/absolute/path/to/device.wvd"
```

```sh
NETFLIX_LICENSE_DEVICE_DIR="/absolute/path/to/exported-folder" make run
```

With this setting, Netflix-DL sends the Python Widevine challenge directly and uses the Python code to process the response. The flow was tested with mocked responses. The local Netflix-DL and Vinetrimmer checkouts yielded no replacement Chrome Widevine credential set, so a successful live license request and a playable download remain unverified.
