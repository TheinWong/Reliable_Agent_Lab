package dev.reliableagentlab.order;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/faults")
@ConditionalOnProperty(name = "app.fault-injection.enabled", havingValue = "true")
public class FaultController {
    private static final Logger log = LoggerFactory.getLogger(FaultController.class);
    private final FaultState faultState;
    private final DemoEventRecorder eventRecorder;

    public FaultController(FaultState faultState, DemoEventRecorder eventRecorder) {
        this.faultState = faultState;
        this.eventRecorder = eventRecorder;
    }

    @GetMapping
    public Map<String, Boolean> status() {
        return Map.of(
                "redisUnavailable", faultState.isRedisUnavailable(),
                "mysqlUnavailable", faultState.isMysqlUnavailable());
    }

    @PutMapping("/redis-unavailable")
    public Map<String, Boolean> injectRedisUnavailable() {
        boolean changed = faultState.setRedisUnavailable(true);
        log.warn("event=demo_fault_injected dependency=redis mode=unavailable changed={}", changed);
        if (changed) {
            eventRecorder.record("demo_fault_injected", "redis", "unavailable");
        }
        return status();
    }

    @DeleteMapping("/redis-unavailable")
    public Map<String, Boolean> resetRedisUnavailable() {
        boolean changed = faultState.setRedisUnavailable(false);
        log.info("event=demo_fault_reset dependency=redis changed={}", changed);
        if (changed) {
            eventRecorder.record("demo_fault_reset", "redis", "normal");
        }
        return status();
    }

    @PutMapping("/mysql-unavailable")
    public Map<String, Boolean> injectMysqlUnavailable() {
        boolean changed = faultState.setMysqlUnavailable(true);
        log.warn("event=demo_fault_injected dependency=mysql mode=unavailable changed={}", changed);
        if (changed) {
            eventRecorder.record("demo_fault_injected", "mysql", "unavailable");
        }
        return status();
    }

    @DeleteMapping("/mysql-unavailable")
    public Map<String, Boolean> resetMysqlUnavailable() {
        boolean changed = faultState.setMysqlUnavailable(false);
        log.info("event=demo_fault_reset dependency=mysql changed={}", changed);
        if (changed) {
            eventRecorder.record("demo_fault_reset", "mysql", "normal");
        }
        return status();
    }
}
