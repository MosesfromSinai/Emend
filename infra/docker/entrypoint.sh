#!/bin/sh
# Named and Railway volumes mount root-owned; the app runs as appuser.
# Fix artifact-dir ownership, then drop privileges.
set -e
ARTIFACTS="${ARTIFACTS_DIR:-/data/artifacts}"
mkdir -p "$ARTIFACTS"
chown appuser:appuser "$ARTIFACTS"
exec gosu appuser "$@"
