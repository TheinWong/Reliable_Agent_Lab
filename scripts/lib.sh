#!/usr/bin/env bash
set -Eeuo pipefail

ORDER_URL="${ORDER_URL:-http://127.0.0.1:${ORDER_SERVICE_PORT:-18080}}"
AGENT_URL="${AGENT_URL:-http://127.0.0.1:${AGENT_API_PORT:-18000}}"

retry() {
  local attempts="$1"
  shift
  local delay_seconds="$1"
  shift
  local attempt
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if "$@"; then
      return 0
    fi
    sleep "$delay_seconds"
  done
  return 1
}

json_field() {
  local field="$1"
  python3 -c 'import json,sys; value=json.load(sys.stdin); print(value[sys.argv[1]])' "$field"
}

wait_for_incident() {
  local incident_id="$1"
  local response=""
  local status=""
  local attempt
  for ((attempt = 1; attempt <= 60; attempt++)); do
    response="$(curl --fail --silent "$AGENT_URL/api/incidents/$incident_id")"
    status="$(printf '%s' "$response" | json_field status)"
    if [[ "$status" == "completed" ]]; then
      printf '%s' "$response"
      return 0
    fi
    if [[ "$status" == "failed" ]]; then
      printf '%s\n' "$response" >&2
      return 1
    fi
    sleep 1
  done
  printf 'incident %s did not complete within 60 seconds\n' "$incident_id" >&2
  return 1
}

wait_for_status() {
  local incident_id="$1"
  local wanted="$2"
  local response=""
  local status=""
  local attempt
  for ((attempt = 1; attempt <= 60; attempt++)); do
    response="$(curl --fail --silent "$AGENT_URL/api/incidents/$incident_id")"
    status="$(printf '%s' "$response" | json_field status)"
    if [[ "$status" == "$wanted" ]]; then
      printf '%s' "$response"
      return 0
    fi
    if [[ "$status" == "failed" && "$wanted" != "failed" ]]; then
      printf '%s\n' "$response" >&2
      return 1
    fi
    sleep 1
  done
  printf 'incident %s did not reach %s within 60 seconds\n' "$incident_id" "$wanted" >&2
  return 1
}
