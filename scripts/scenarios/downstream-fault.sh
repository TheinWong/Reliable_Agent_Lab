#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib.sh"

case "${1:-}" in
  inventory-latency)
    service="inventory-service"
    base_url="http://127.0.0.1:${INVENTORY_SERVICE_PORT:-18081}"
    fault_path="inventory-latency"
    fault_field="inventoryLatency"
    action="reset_inventory_latency"
    diagnosis="controlled inventory downstream latency detected"
    hypothesis="Inventory downstream latency"
    scenario_id="s3-inventory-latency"
    symptom="Checkout preview inventory call is slow after controlled injection"
    ;;
  payment-5xx)
    service="payment-service"
    base_url="http://127.0.0.1:${PAYMENT_SERVICE_PORT:-18082}"
    fault_path="payment-5xx"
    fault_field="paymentHttp5xx"
    action="reset_payment_5xx"
    diagnosis="controlled payment downstream HTTP 5xx detected"
    hypothesis="Payment downstream HTTP 5xx"
    scenario_id="s4-payment-5xx"
    symptom="Checkout preview payment call fails after controlled injection"
    ;;
  *) echo "usage: $0 inventory-latency|payment-5xx" >&2; exit 2 ;;
esac

cleanup() {
  curl --fail --silent -X DELETE "$base_url/internal/faults/$fault_path" >/dev/null || true
}
trap cleanup EXIT
cleanup
order_faults="$(curl --fail --silent "$ORDER_URL/internal/faults")"
[[ "$(printf '%s' "$order_faults" | json_field redisUnavailable)" == "False" ]]
[[ "$(printf '%s' "$order_faults" | json_field mysqlUnavailable)" == "False" ]]
if [[ "$service" == "inventory-service" ]]; then
  other_url="http://127.0.0.1:${PAYMENT_SERVICE_PORT:-18082}"
  other_field="paymentHttp5xx"
else
  other_url="http://127.0.0.1:${INVENTORY_SERVICE_PORT:-18081}"
  other_field="inventoryLatency"
fi
[[ "$(curl --fail --silent "$other_url/internal/faults" | json_field "$other_field")" == "False" ]]
injected="$(curl --fail --silent -X PUT "$base_url/internal/faults/$fault_path")"
started_at="$(printf '%s' "$injected" | json_field faultStartedAt)"
[[ "$(printf '%s' "$injected" | json_field "$fault_field")" == "True" ]]

response_file="$(mktemp)"
trap 'cleanup; rm -f "$response_file"' EXIT
status="$(curl --silent --output "$response_file" --write-out '%{http_code}' "$ORDER_URL/api/orders/1/checkout-preview")"
if [[ "$service" == "inventory-service" ]]; then
  [[ "$status" == "200" ]]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["status"]=="OK" and d["inventoryLatencyMs"]>=500' "$response_file"
else
  [[ "$status" == "502" ]]
  python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["error"]["code"]=="PAYMENT_UNAVAILABLE"' "$response_file"
fi

uv run python "$SCRIPT_DIR/verify_downstream_trace.py" "$service" "$started_at" \
  --jaeger-url "http://127.0.0.1:${JAEGER_UI_PORT:-16686}"

payload="$(python3 -c 'import json,sys; print(json.dumps({"service":"order-service","symptom":sys.argv[1],"scenario_id":sys.argv[2]}))' "$symptom" "$scenario_id")"
created="$(curl --fail --silent -H 'Content-Type: application/json' -d "$payload" "$AGENT_URL/api/incidents")"
incident_id="$(printf '%s' "$created" | json_field id)"
paused="$(wait_for_status "$incident_id" awaiting_approval)"
printf '%s' "$paused" | python3 -c \
  'import json,sys; d=json.load(sys.stdin); expected=sys.argv[1:]; reports={r["role"]:r for r in d["specialist_reports"]}; assert expected[0] in d["diagnosis"]; assert d["remediation_plan"]["action"]==expected[1]; assert set(reports)=={"metrics","logs","trace"}; assert all(r["status"]=="complete" for r in reports.values()); assert expected[2] in reports["trace"]["hypotheses"]' \
  "$diagnosis" "$action" "$hypothesis" >/dev/null

[[ "$(curl --fail --silent "$base_url/internal/faults" | json_field "$fault_field")" == "True" ]]
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
  'import json,sys; d=json.load(sys.stdin); assert d["approval"]=="approved"; assert d["execution"]["status"]=="completed"; v=d["verification"]; assert v["status"]=="resolved" and v["fault_cleared"] is True; assert v["preview_status"]=="OK" and v["payment_authorized"] is True; assert v["inventory_latency_ms"]<500'
curl --fail --silent -H 'Content-Type: application/json' -d "$approval_payload" \
  "$AGENT_URL/api/incidents/$incident_id/approval" >/dev/null
action_rows="$(docker compose exec -T postgres psql -U agentlab -d agentlab -t -A -c "SELECT count(*) FROM ral_action_executions WHERE action_id = '$action_id'")"
[[ "$action_rows" == "1" ]]
[[ "$(curl --fail --silent "$base_url/internal/faults" | json_field "$fault_field")" == "False" ]]
run_id="$(printf '%s' "$result" | json_field run_id)"
uv run python "$SCRIPT_DIR/verify_traces.py" "$incident_id" "$run_id" \
  --action "$action" --jaeger-url "http://127.0.0.1:${JAEGER_UI_PORT:-16686}"
printf 'scenario passed: %s incident=%s\n' "$scenario_id" "$incident_id"
