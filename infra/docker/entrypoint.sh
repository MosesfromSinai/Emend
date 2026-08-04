#!/bin/sh
# Named and Railway volumes mount root-owned; the app runs as appuser.
# Fix artifact-dir ownership, then drop privileges.
set -e
ARTIFACTS="${ARTIFACTS_DIR:-/data/artifacts}"
mkdir -p "$ARTIFACTS"
chown appuser:appuser "$ARTIFACTS"
# Railway assigns its own PORT and healthchecks that port directly; compose
# and other hosts get the Dockerfile's default of 8000. Only the actual
# server process takes --port, though -- Railway's preDeployCommand and any
# other one-off invocation (alembic, a shell) go through this same
# entrypoint, and blindly appending --port to those broke `alembic upgrade
# head` outright (it doesn't recognize the flag and refuses to run at all).
if [ "$1" = "uvicorn" ]; then
    exec gosu appuser "$@" --port "${PORT:-8000}"
fi
exec gosu appuser "$@"
