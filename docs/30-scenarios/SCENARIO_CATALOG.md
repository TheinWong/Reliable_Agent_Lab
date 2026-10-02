# Scenario Catalog — v0.1 Target

## S1 Redis unavailable / timeout
Primary evidence: health, logs, Redis-related metrics.
Expected investigation: Metrics + Logs; Trace may be optional depending on implementation.
Expected action: restore/reset the controlled Redis fault.

## S2 Controlled MySQL read failure
Primary evidence: uncached order 503, application read-failure counter and bounded event. This does not simulate a physical network outage or pool exhaustion.
Expected action: reset the local application-boundary read fault; verify database read then cache hit.

## S3 Inventory downstream latency
Primary evidence: checkout-preview latency, current inventory fault state, fresh order event, and a post-injection slow inventory-service span in the same trace.
Expected investigation: Metrics + Trace + Logs.
Expected action: reset artificial latency/fault.

## S4 Payment HTTP 5xx
Primary evidence: payment-service HTTP 503 span, order-service HTTP 502 and fresh bounded event. Payment is a stateless preview, not a charge.
Expected action: reset payment fault.

## Stretch S5 Cascading timeout
Purpose: test evidence conflict/fan-out and trace topology.

## Stretch S6 Cache inconsistency
Purpose: health may look normal while business result is wrong; tests verification beyond health endpoint.

v0.1 release requires at least four fully automated scenarios. Stretch scenarios may be deferred if they threaten release quality.
