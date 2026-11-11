$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectDirectory 'compose.yaml'
$dockerArguments = @('compose', '-f', $composeFile, 'run', '--rm', '--build')

if ($env:NETFLIX_LICENSE_DEVICE_DIR) {
    $device = Get-Item -LiteralPath $env:NETFLIX_LICENSE_DEVICE_DIR
    if ($device -isnot [System.IO.DirectoryInfo]) {
        throw 'NETFLIX_LICENSE_DEVICE_DIR must point to a directory.'
    }

    foreach ($file in @('device_private_key', 'device_client_id_blob')) {
        if (-not (Test-Path -LiteralPath (Join-Path $device.FullName $file) -PathType Leaf)) {
            throw "NETFLIX_LICENSE_DEVICE_DIR is missing $file."
        }
    }

    $containerDeviceDirectory = '/run/netflix-license-device'
    $dockerArguments += @(
        '--volume', "$($device.FullName):${containerDeviceDirectory}:ro",
        '--env', "NETFLIX_LICENSE_DEVICE_DIR=$containerDeviceDirectory"
    )
}

$dockerArguments += 'netflix-dl'
$dockerArguments += $args
& docker @dockerArguments
exit $LASTEXITCODE
