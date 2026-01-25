#!/bin/sh
set -eu

CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/TinyPedal/launcher.conf"
if [ -f "${CONFIG_FILE}" ] && [ -z "${TINYPEDAL_RUN_ARGS:-}" ];
then
    . "${CONFIG_FILE}"
fi

./run.py ${TINYPEDAL_RUN_ARGS:-} "$@"
