#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib.sh"

cleanup() {
  curl --fail --silent -X DELETE "$ORDER_URL/internal/faults/mysql-unavailable" >/dev/null || true
}
trap cleanup EXIT

cleanup
docker compose exec -T redis redis-cli DEL order:1 >/dev/null
curl --fail --silent -X PUT "$ORDER_URL/internal/faults/mysql-unavailable" >/dev/null

response_file="$(mktemp)"
trap 'cleanup; rm -f "$response_file"' EXIT
status="$(curl --silent --output "$response_file" --write-out '%{http_code}' "$ORDER_URL/api/orders/1")"
[[ "$status" == "503" ]]
python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["error"]["code"]=="DEMO_MYSQL_UNAVAILABLE"' "$response_file"

created="$(curl --fail --silent \
  -H 'Content-Type: application/json' \
  -d '{"service":"order-service","symptom":"Uncached order read returns 503 from controlled MySQL failure","scenario_id":"s2-mysql-unavailable"}' \
  "$AGENT_URL/api/incidents")"
incident_id="$(printf '%s' "$created" | json_field id)"
paused="$(wait_for_status "$incident_id" awaiting_approval)"
printf '%s' "$paused" | python3 -c \
  'import json,sys; data=json.load(sys.stdin); reports={x["role"]:x for x in data["specialist_reports"]}; assert "MySQL unavailability" in data["diagnosis"]; assert {"metrics","logs","trace"}==set(reports); assert reports["metrics"]["status"]==reports["logs"]["status"]=="complete"; assert data["remediation_plan"]["action"]=="reset_mysql_fault"'
[[ "$(curl --fail --silent "$ORDER_URL/internal/faults" | json_field mysqlUnavailable)" == "True" ]]

docker compose restart agent-api >/dev/null
retry 30 1 curl --fail --silent "$AGENT_URL/health" >/dev/null
persisted="$(curl --fail --silent "$AGENT_URL/api/incidents/$incident_id")"
[[ "$(printf '%s' "$persisted" | json_field status)" == "awaiting_approval" ]]
action_id="$(printf '%s' "$persisted" | python3 -c 'import json,sys; print(json.load(sys.stdin)["remediation_plan"]["action_id"])')"
approval_payload="$(python3 -c 'import json,sys; print(json.dumps({"action_id":sys.argv[1],"approved":True}))' "$action_id")"
curl --fail --silent -H 'Content-Type: application/json' -d "$approval_payload" \
  "$AGENT_URL/api/incidents/$incident_id/approval" >/dev/null
result="$(wait_for_incident "$incident_id")"
printf '%s' "$result" | python3 -c \
  'import json,sys; d=json.load(sys.stdin); assert d["approval"]=="approved"; assert d["execution"]["status"]=="completed"; assert d["verification"]["status"]=="resolved"; assert d["verification"]["fault_cleared"] is True; assert (d["verification"]["first_source"],d["verification"]["second_source"])==("DATABASE","CACHE")'
curl --fail --silent -H 'Content-Type: application/json' -d "$approval_payload" \
  "$AGENT_URL/api/incidents/$incident_id/approval" >/dev/null
action_rows="$(docker compose exec -T postgres psql -U agentlab -d agentlab -t -A -c "SELECT count(*) FROM ral_action_executions WHERE action_id = '$action_id'")"
[[ "$action_rows" == "1" ]]
[[ "$(curl --fail --silent "$ORDER_URL/internal/faults" | json_field mysqlUnavailable)" == "False" ]]

docker compose exec -T redis redis-cli DEL order:1 >/dev/null
first="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
second="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
[[ "$(printf '%s' "$first" | json_field source)" == "DATABASE" ]]
[[ "$(printf '%s' "$second" | json_field source)" == "CACHE" ]]
run_id="$(printf '%s' "$result" | json_field run_id)"
uv run python "$SCRIPT_DIR/verify_traces.py" "$incident_id" "$run_id" \
  --action reset_mysql_fault --jaeger-url "http://127.0.0.1:${JAEGER_UI_PORT:-16686}"
printf 'scenario passed: s2-mysql-unavailable incident=%s\n' "$incident_id"
