#!/usr/bin/env bash

set -euo pipefail

scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${scenario_dir}/../.." && pwd)"
compose=(docker compose -f "${repo_root}/infra/docker-compose.yml")
base_url="${DEMO_SERVICE_URL:-http://localhost:8080}"
work_dir="$(mktemp -d)"

cleanup() {
    "${compose[@]}" start redis >/dev/null 2>&1 || true
    rm -rf "${work_dir}"
}
trap cleanup EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

request_status() {
    local method="$1"
    local url="$2"
    local output_file="$3"
    shift 3
    curl --max-time 5 --silent --show-error \
        --request "${method}" \
        --output "${output_file}" \
        --write-out '%{http_code}' \
        "$@" \
        "${url}"
}

wait_for_healthy_service() {
    local attempts="${1:-30}"

    for ((attempt = 1; attempt <= attempts; attempt++)); do
        if curl --max-time 5 --fail --silent "${base_url}/actuator/health" \
            | grep -q '"redis":{"status":"UP"'; then
            return 0
        fi
        sleep 1
    done

    fail "service did not report Redis UP"
}

metric_value() {
    local metric="$1"
    local tag_name="$2"
    local tag_value="$3"
    local sample="${metric}{${tag_name}=\"${tag_value}\"}"

    curl --max-time 5 --fail --silent "${base_url}/actuator/prometheus" \
        | awk -v sample="${sample}" '$1 == sample { print $2; exit }'
}

assert_equal() {
    local actual="$1"
    local expected="$2"
    local description="$3"

    [[ "${actual}" == "${expected}" ]] \
        || fail "${description}: expected ${expected}, got ${actual}"
}

assert_incremented_by_one() {
    local before="$1"
    local after="$2"
    local description="$3"

    awk -v before="${before}" -v after="${after}" \
        'BEGIN { exit !((after - before) == 1) }' \
        || fail "${description}: expected ${before} + 1, got ${after}"
}

echo "Starting the healthy environment"
"${compose[@]}" up -d --build
wait_for_healthy_service

create_status="$(request_status POST "${base_url}/api/orders" "${work_dir}/create.json" \
    --header 'Content-Type: application/json' \
    --data '{"productId":2001,"quantity":2}')"
assert_equal "${create_status}" "201" "create order status"

order_id="$(sed -n 's/.*"id":\([0-9][0-9]*\).*/\1/p' "${work_dir}/create.json")"
[[ -n "${order_id}" ]] || fail "created order response did not contain an id"
cache_key="order:${order_id}"

echo "Verifying cache miss, population, and hit"
"${compose[@]}" exec -T redis redis-cli DEL "${cache_key}" >/dev/null

miss_before="$(metric_value order_cache_reads_total result miss)"
fallback_miss_before="$(metric_value order_mysql_fallbacks_total reason cache_miss)"
write_success_before="$(metric_value order_cache_writes_total result success)"

first_read_status="$(request_status GET "${base_url}/api/orders/${order_id}" "${work_dir}/first-read.json")"
assert_equal "${first_read_status}" "200" "cache-miss order read status"
assert_incremented_by_one "${miss_before}" \
    "$(metric_value order_cache_reads_total result miss)" "cache miss counter"
assert_incremented_by_one "${fallback_miss_before}" \
    "$(metric_value order_mysql_fallbacks_total reason cache_miss)" "cache-miss fallback counter"
assert_incremented_by_one "${write_success_before}" \
    "$(metric_value order_cache_writes_total result success)" "successful cache write counter"

hit_before="$(metric_value order_cache_reads_total result hit)"
second_read_status="$(request_status GET "${base_url}/api/orders/${order_id}" "${work_dir}/second-read.json")"
assert_equal "${second_read_status}" "200" "cache-hit order read status"
assert_incremented_by_one "${hit_before}" \
    "$(metric_value order_cache_reads_total result hit)" "cache hit counter"

echo "Stopping Redis and verifying bounded MySQL fallback"
error_before="$(metric_value order_cache_reads_total result error)"
fallback_error_before="$(metric_value order_mysql_fallbacks_total reason cache_error)"
skipped_before="$(metric_value order_cache_writes_total result skipped)"
hit_before_fault="$(metric_value order_cache_reads_total result hit)"

"${compose[@]}" stop redis
degraded_status="$(request_status GET "${base_url}/api/orders/${order_id}" "${work_dir}/degraded-read.json")"
assert_equal "${degraded_status}" "200" "degraded order read status"

assert_incremented_by_one "${error_before}" \
    "$(metric_value order_cache_reads_total result error)" "cache error counter"
assert_incremented_by_one "${fallback_error_before}" \
    "$(metric_value order_mysql_fallbacks_total reason cache_error)" "cache-error fallback counter"
assert_incremented_by_one "${skipped_before}" \
    "$(metric_value order_cache_writes_total result skipped)" "skipped cache write counter"
assert_equal "$(metric_value order_cache_reads_total result hit)" \
    "${hit_before_fault}" "cache hit counter during outage"

health_status="$(request_status GET "${base_url}/actuator/health" "${work_dir}/degraded-health.json")"
assert_equal "${health_status}" "503" "degraded health status"
grep -q '"redis":{"status":"DOWN"' "${work_dir}/degraded-health.json" \
    || fail "degraded health did not report Redis DOWN"
"${compose[@]}" logs --since=2m demo-service >"${work_dir}/demo-service.log"
grep -q 'event=order_cache_read_failed' "${work_dir}/demo-service.log" \
    || fail "cache read failure log was not found"

echo "Starting Redis and verifying application-level recovery"
"${compose[@]}" start redis
wait_for_healthy_service 45
"${compose[@]}" exec -T redis redis-cli DEL "${cache_key}" >/dev/null

cache_populated=false
for ((attempt = 1; attempt <= 30; attempt++)); do
    recovery_status="$(request_status GET "${base_url}/api/orders/${order_id}" "${work_dir}/recovery-read.json")"
    assert_equal "${recovery_status}" "200" "recovery order read status"
    if [[ "$("${compose[@]}" exec -T redis redis-cli EXISTS "${cache_key}")" == "1" ]]; then
        cache_populated=true
        break
    fi
    sleep 1
done
[[ "${cache_populated}" == "true" ]] || fail "cache was not repopulated after Redis recovery"

recovered_error="$(metric_value order_cache_reads_total result error)"
recovered_fallback_error="$(metric_value order_mysql_fallbacks_total reason cache_error)"
recovered_hit_before="$(metric_value order_cache_reads_total result hit)"

final_status="$(request_status GET "${base_url}/api/orders/${order_id}" "${work_dir}/final-read.json")"
assert_equal "${final_status}" "200" "post-recovery cache-hit status"
assert_incremented_by_one "${recovered_hit_before}" \
    "$(metric_value order_cache_reads_total result hit)" "post-recovery cache hit counter"
assert_equal "$(metric_value order_cache_reads_total result error)" \
    "${recovered_error}" "post-recovery cache error counter"
assert_equal "$(metric_value order_mysql_fallbacks_total reason cache_error)" \
    "${recovered_fallback_error}" "post-recovery fallback error counter"

echo "PASS: Redis unavailable scenario verified for order ${order_id}"
