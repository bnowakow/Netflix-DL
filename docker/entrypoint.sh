#!/bin/sh
set -eu

case "${1-}" in
    "")
        exec python run_dialog.py
        ;;
    wine-check)
        exec python -c 'from helpers.Parsers.Netflix.get_keys import check_wine_helper; check_wine_helper()'
        ;;
    *)
        exec python NFripper.py "$@"
        ;;
esac
