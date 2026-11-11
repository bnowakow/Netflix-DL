"""Export the device files used by Netflix-DL from an existing WVD."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def export_device(wvd, destination, cli):
    with TemporaryDirectory(prefix="netflix-license-device-") as temporary:
        subprocess.run(
            [cli, "export-device", "-o", temporary, str(wvd)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        exported = Path(temporary) / wvd.stem
        credentials = {
            "device_private_key": (exported / "private_key.der").read_bytes(),
            "device_client_id_blob": (exported / "client_id.bin").read_bytes(),
        }
        if not all(credentials.values()):
            raise ValueError("The WVD export is missing a private key or client ID.")
        vmp = exported / "vmp.bin"
        if vmp.is_file():
            credentials["device_vmp_blob"] = vmp.read_bytes()

    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name in ("device_private_key", "device_client_id_blob", "device_vmp_blob"):
        if os.path.lexists(destination / name):
            raise FileExistsError(f"{destination / name} already exists. Use a fresh directory.")

    created = []
    try:
        for name, data in credentials.items():
            path = destination / name
            with open(path, "xb", opener=lambda file, flags: os.open(file, flags, 0o600)) as output:
                created.append(path)
                output.write(data)
    except BaseException:
        for path in created:
            path.unlink()
        raise


def main():
    if len(sys.argv) != 2 or not sys.argv[1]:
        raise SystemExit('Supply the input file with make export-license-device WVD="path/to/device.wvd".')
    wvd = Path(sys.argv[1]).expanduser().resolve()
    if not wvd.is_file() or wvd.suffix.lower() != ".wvd":
        raise SystemExit("WVD must point to an existing .wvd file.")
    directory = os.environ.get("NETFLIX_LICENSE_DEVICE_DIR")
    if not directory:
        raise SystemExit("Set NETFLIX_LICENSE_DEVICE_DIR to the desired output directory.")
    cli = shutil.which("pywidevine")
    if not cli:
        raise SystemExit("Install the standalone Pywidevine CLI and put it on PATH.")

    destination = Path(directory).expanduser().resolve()
    try:
        export_device(wvd, destination, cli)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Device export failed: {error}") from None
    print(f"Exported Widevine device files to {destination}")


if __name__ == "__main__":
    main()
