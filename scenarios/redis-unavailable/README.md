# Redis Unavailable Scenario

**Status:** implemented and locally verified on 2026-09-22

## Purpose

Demonstrate that the Order Service can detect a real Redis dependency outage,
continue serving order reads through a bounded MySQL fallback, expose clear
diagnostic evidence, and verify that caching works again after recovery.

MySQL is the source of truth. Redis is a cache-aside optimization for order
detail reads.

## Preconditions

- The local Docker Compose environment is healthy.
- The Order Service, MySQL, and Redis are running.
- A known order exists in MySQL.
- A healthy order read can populate Redis and a repeated read can hit the
  cache.

## Fault

Stop only the allow-listed Redis service in the local demo environment:

```bash
docker compose -f infra/docker-compose.yml stop redis
```

This is a real dependency outage. The application must not simulate the
failure with an in-process fault flag.

## Expected symptoms

- Redis cache reads fail.
- Order reads fall back to MySQL.
- Existing orders remain readable while MySQL is healthy.
- Read latency may increase during fallback.
- Redis dependency health reports an unhealthy state.

## Expected evidence

- Spring Boot Actuator reports the Redis dependency as `DOWN`.
- Structured application logs record the Redis access failure and MySQL
  fallback without exposing credentials.
- The cache-read failure counter increases.
- The MySQL-fallback counter increases.
- The cache-hit counter stops increasing while Redis is unavailable.

The Prometheus endpoint exposes the following bounded-label counters:

- `order_cache_reads_total{result="hit|miss|error"}`;
- `order_mysql_fallbacks_total{reason="cache_miss|cache_error"}`;
- `order_cache_writes_total{result="success|error|skipped"}`.

No order ID or other unbounded value is used as a metric label.

## Ground-truth root cause

The Redis container is stopped, so the Order Service cannot establish a Redis
connection. Order data is not lost because MySQL remains the authoritative
store.

## Expected remediation

Start only the allow-listed Redis service:

```bash
docker compose -f infra/docker-compose.yml start redis
```

A successful command response proves only that the recovery action was
accepted. It does not prove that Redis or the application cache path has
recovered.

## Verification criteria

Recovery succeeds only when all deterministic criteria pass:

1. The Redis container is running.
2. Spring Boot Actuator reports the Redis dependency as `UP`.
3. An order detail request succeeds.
4. A post-recovery cache miss can read the order from MySQL and repopulate
   Redis.
5. A repeated read of the same order produces a cache hit.
6. New reads no longer increase the Redis failure or MySQL-fallback counters.

Latency should also return near the measured healthy baseline. It is
supporting evidence until the project has enough measurements to define a
stable threshold.

Redis container readiness may precede recovery of the application's existing
Lettuce connections. Verification therefore waits for application health and
then proves that the synchronous cache path can populate and hit a key. Do not
treat `docker compose start redis` alone as successful recovery.

## Automated verification

Run the complete healthy, degraded, and recovered sequence from the repository
root:

```bash
./scenarios/redis-unavailable/verify.sh
```

The script builds and starts the Compose environment, creates a fresh order,
checks cache miss and hit metrics, stops Redis, verifies the `200` MySQL
fallback and degraded evidence, restarts Redis, and proves cache population and
subsequent cache hits. A cleanup trap starts Redis if verification exits early.

## Verification failure

Do not mark the incident resolved when the container starts but Redis health
remains `DOWN`, or when order reads succeed but the cache cannot be populated
and hit again. Collect fresh health, connection, and cache-write evidence
before choosing another bounded action.

## Safety boundary

Fault and recovery commands target only the local Compose service named
`redis`. This scenario does not authorize arbitrary shell execution, arbitrary
container control, or access to production infrastructure.
