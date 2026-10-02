#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

retry 30 1 curl --fail --silent "$ORDER_URL/actuator/health/readiness" >/dev/null
retry 30 1 curl --fail --silent "$AGENT_URL/health" >/dev/null

docker compose exec -T redis redis-cli DEL order:1 >/dev/null
first_read="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
second_read="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
[[ "$(printf '%s' "$first_read" | json_field source)" == "DATABASE" ]]
[[ "$(printf '%s' "$second_read" | json_field source)" == "CACHE" ]]

created="$(curl --fail --silent \
  -H 'Content-Type: application/json' \
  -d '{"service":"order-service","symptom":"verify healthy order path"}' \
  "$AGENT_URL/api/incidents")"
incident_id="$(printf '%s' "$created" | json_field id)"
result="$(wait_for_incident "$incident_id")"
[[ "$(printf '%s' "$result" | json_field status)" == "completed" ]]
printf '%s' "$result" | python3 -c \
  'import json,sys; reports=json.load(sys.stdin)["specialist_reports"]; assert {item["role"] for item in reports}=={"metrics","logs","trace"}'
printf 'smoke passed: incident=%s\n' "$incident_id"
