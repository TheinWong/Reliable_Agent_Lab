package dev.reliableagentlab.order;

import java.util.List;
import java.util.Map;

import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/evidence")
@ConditionalOnProperty(name = "app.fault-injection.enabled", havingValue = "true")
public class DemoEvidenceController {
    private final FaultState faultState;
    private final DemoEventRecorder recorder;
    private final MeterRegistry metrics;

    public DemoEvidenceController(FaultState faultState, DemoEventRecorder recorder, MeterRegistry metrics) {
        this.faultState = faultState;
        this.recorder = recorder;
        this.metrics = metrics;
    }

    @GetMapping("/metrics")
    public Map<String, Object> metrics() {
        return Map.of(
                "service", "order-service",
                "redisUnavailable", faultState.isRedisUnavailable(),
                "mysqlUnavailable", faultState.isMysqlUnavailable(),
                "cacheReadErrors", counter("order.cache.reads", "result", "error"),
                "mysqlCacheErrorFallbacks", counter("order.mysql.fallbacks", "reason", "cache_error"),
                "mysqlControlledFailures", counter("order.mysql.failures", "reason", "controlled_unavailable"),
                "inventorySlowRequests", counter("order.inventory.requests", "result", "slow"),
                "paymentPreviewErrors", counter("order.payment.requests", "result", "error"));
    }

    @GetMapping("/logs")
    public Map<String, List<DemoEventRecorder.DemoEvent>> logs() {
        return Map.of("events", recorder.recent());
    }

    private double counter(String name, String tag, String value) {
        var meter = metrics.find(name).tag(tag, value).counter();
        return meter == null ? 0.0 : meter.count();
    }
}
