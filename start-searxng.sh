#!/bin/bash
set -euo pipefail

ARMADA_DIR="${ARMADA_DIR:-$HOME/armada}"
SEARXNG_DIR="${SEARXNG_DIR:-$ARMADA_DIR/searxng}"
VENV_DIR="${SEARXNG_VENV:-$SEARXNG_DIR/venv}"
SETTINGS_PATH="${SEARXNG_SETTINGS_PATH:-$SEARXNG_DIR/searx/settings.yml}"
LOG_DIR="${ARMADA_LOG_DIR:-$ARMADA_DIR/logs}"
LOG_FILE="$LOG_DIR/searxng.log"
PID_FILE="$LOG_DIR/searxng.pid"

mkdir -p "$LOG_DIR"

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(< "$PID_FILE")" >/dev/null 2>&1
}

case "${1:-start}" in
  start)
    if is_running; then
      printf 'SearXNG already running with PID %s\n' "$(< "$PID_FILE")"
      exit 0
    fi

    cd "$SEARXNG_DIR"
    export SEARXNG_SETTINGS_PATH="$SETTINGS_PATH"
    export SEARXNG_BIND_ADDRESS="127.0.0.1"
    export SEARXNG_PORT="8888"
    export SEARXNG_LIMITER="false"
    nohup "$VENV_DIR/bin/searxng-run" >> "$LOG_FILE" 2>&1 &
    printf '%s\n' "$!" > "$PID_FILE"
    printf 'SearXNG started with PID %s; log: %s\n' "$!" "$LOG_FILE"
    ;;
  foreground)
    cd "$SEARXNG_DIR"
    export SEARXNG_SETTINGS_PATH="$SETTINGS_PATH"
    export SEARXNG_BIND_ADDRESS="127.0.0.1"
    export SEARXNG_PORT="8888"
    export SEARXNG_LIMITER="false"
    exec "$VENV_DIR/bin/searxng-run"
    ;;
  stop)
    if is_running; then
      kill "$(< "$PID_FILE")"
      rm -f "$PID_FILE"
      printf 'SearXNG stopped\n'
    else
      rm -f "$PID_FILE"
      printf 'SearXNG is not running\n'
    fi
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    if is_running; then
      printf 'SearXNG running with PID %s\n' "$(< "$PID_FILE")"
    else
      printf 'SearXNG is not running\n'
      exit 1
    fi
    ;;
  *)
    printf 'Usage: %s [start|stop|restart|status|foreground]\n' "$0" >&2
    exit 2
    ;;
esac
