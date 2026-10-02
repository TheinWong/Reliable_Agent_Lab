#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib.sh"

cleanup() {
  curl --fail --silent -X DELETE "$ORDER_URL/internal/faults/redis-unavailable" >/dev/null || true
}
trap cleanup EXIT

cleanup
docker compose exec -T redis redis-cli DEL order:1 >/dev/null
curl --fail --silent -X PUT "$ORDER_URL/internal/faults/redis-unavailable" >/dev/null

degraded_read="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
[[ "$(printf '%s' "$degraded_read" | json_field source)" == "DATABASE" ]]
[[ "$(printf '%s' "$degraded_read" | json_field cacheDegraded)" == "True" ]]

created="$(curl --fail --silent \
  -H 'Content-Type: application/json' \
  -d '{"service":"order-service","symptom":"Redis unavailable with MySQL fallback","scenario_id":"s1-redis-unavailable"}' \
  "$AGENT_URL/api/incidents")"
incident_id="$(printf '%s' "$created" | json_field id)"
paused="$(wait_for_status "$incident_id" awaiting_approval)"
printf '%s' "$paused" | python3 -c \
  'import json,sys; data=json.load(sys.stdin); assert "Redis unavailability" in data["diagnosis"]; reports={item["role"]: item for item in data["specialist_reports"]}; assert set(reports)=={"metrics","logs","trace"}; assert all(reports[role]["status"]=="complete" for role in reports); assert all(reports[role]["evidence_refs"] for role in reports); assert data["remediation_plan"]["action"]=="reset_redis_fault"'
[[ "$(curl --fail --silent "$ORDER_URL/internal/faults" | json_field redisUnavailable)" == "True" ]]
docker compose restart agent-api >/dev/null
retry 30 1 curl --fail --silent "$AGENT_URL/health" >/dev/null
persisted="$(curl --fail --silent "$AGENT_URL/api/incidents/$incident_id")"
[[ "$(printf '%s' "$persisted" | json_field status)" == "awaiting_approval" ]]
events="$(curl --fail --silent --max-time 5 "$AGENT_URL/api/incidents/$incident_id/events")"
printf '%s' "$events" | python3 -c \
  'import sys; value=sys.stdin.read(); assert value.count("event: delegation.started") == 3; assert value.count("event: delegation.completed") == 3; assert "event: diagnosis.updated" in value; assert "event: approval.required" in value'
docker compose logs --no-color order-service | grep -F 'event=order_cache_read_failed' >/dev/null

action_id="$(printf '%s' "$persisted" | python3 -c 'import json,sys; print(json.load(sys.stdin)["remediation_plan"]["action_id"])')"
approval_payload="$(python3 -c 'import json,sys; print(json.dumps({"action_id":sys.argv[1],"approved":True}))' "$action_id")"
curl --fail --silent -H 'Content-Type: application/json' -d "$approval_payload" \
  "$AGENT_URL/api/incidents/$incident_id/approval" >/dev/null
result="$(wait_for_incident "$incident_id")"
printf '%s' "$result" | python3 -c \
  'import json,sys; data=json.load(sys.stdin); assert data["approval"]=="approved"; assert data["execution"]["status"]=="completed"; assert data["verification"]["status"]=="resolved"; assert data["verification"]["fault_cleared"] is True; assert data["verification"]["first_source"]=="DATABASE"; assert data["verification"]["second_source"]=="CACHE"'
curl --fail --silent -H 'Content-Type: application/json' -d "$approval_payload" \
  "$AGENT_URL/api/incidents/$incident_id/approval" >/dev/null
completed_events="$(curl --fail --silent --max-time 5 "$AGENT_URL/api/incidents/$incident_id/events")"
printf '%s' "$completed_events" | python3 -c \
  'import json,sys; events=[json.loads(line.removeprefix("data: ")) for line in sys.stdin if line.startswith("data: ")]; starts=[event for event in events if event["type"]=="tool.started" and event["data"].get("agent")=="remediation"]; done=[event for event in events if event["type"]=="tool.completed" and event["data"].get("agent")=="remediation"]; assert len(starts)==len(done)==1; assert sum(event["type"]=="verification.completed" for event in events)==1'
action_rows="$(docker compose exec -T postgres psql -U agentlab -d agentlab -t -A -c "SELECT count(*) FROM ral_action_executions WHERE action_id = '$action_id'")"
[[ "$action_rows" == "1" ]]
[[ "$(curl --fail --silent "$ORDER_URL/internal/faults" | json_field redisUnavailable)" == "False" ]]

docker compose exec -T redis redis-cli DEL order:1 >/dev/null
repopulate="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
cache_hit="$(curl --fail --silent "$ORDER_URL/api/orders/1")"
[[ "$(printf '%s' "$repopulate" | json_field source)" == "DATABASE" ]]
[[ "$(printf '%s' "$cache_hit" | json_field source)" == "CACHE" ]]
run_id="$(printf '%s' "$result" | json_field run_id)"
uv run python "$SCRIPT_DIR/verify_traces.py" "$incident_id" "$run_id" \
  --jaeger-url "http://127.0.0.1:${JAEGER_UI_PORT:-16686}"
printf 'scenario passed: s1-redis-unavailable incident=%s\n' "$incident_id"
