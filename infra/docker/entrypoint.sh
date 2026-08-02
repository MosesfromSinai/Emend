#!/bin/sh
# Named and Railway volumes mount root-owned; the app runs as appuser.
# Fix artifact-dir ownership, then drop privileges.
set -e
ARTIFACTS="${ARTIFACTS_DIR:-/data/artifacts}"
mkdir -p "$ARTIFACTS"
chown appuser:appuser "$ARTIFACTS"
# Railway assigns its own PORT and healthchecks that port directly; compose
# and other hosts get the Dockerfile's default of 8000.
exec gosu appuser "$@" --port "${PORT:-8000}"
