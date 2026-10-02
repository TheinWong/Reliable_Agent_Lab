package dev.reliableagentlab.downstream;

import java.util.Map;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@ConditionalOnProperty(name = "app.role", havingValue = "inventory")
public class InventoryController {
    private static final Logger log = LoggerFactory.getLogger(InventoryController.class);
    private final FaultState faultState;
    private final Counter slowRequests;
    private final boolean demoFaultsEnabled;

    public InventoryController(FaultState faultState, MeterRegistry registry,
            @Value("${app.fault-injection.enabled:false}") boolean demoFaultsEnabled) {
        this.faultState = faultState;
        this.slowRequests = registry.counter("inventory.requests", "result", "slow");
        this.demoFaultsEnabled = demoFaultsEnabled;
    }

    @GetMapping("/api/inventory/{sku}")
    public ResponseEntity<Map<String, Object>> availability(@PathVariable String sku) throws InterruptedException {
        if (faultState.isActive()) {
            slowRequests.increment();
            log.warn("event=inventory_latency_injected sku={} delayMs=800", sku);
            Thread.sleep(800);
        }
        return ResponseEntity.ok(Map.of("sku", sku, "available", true));
    }

    @GetMapping("/internal/faults")
    public Map<String, Object> status() {
        return Map.of("inventoryLatency", faultState.isActive(),
                "faultStartedAt", faultState.activatedAt());
    }

    @PutMapping("/internal/faults/inventory-latency")
    public Map<String, Object> inject() {
        requireDemoMode();
        boolean changed = faultState.setActive(true);
        log.warn("event=demo_fault_injected dependency=inventory mode=latency changed={}", changed);
        return status();
    }

    @DeleteMapping("/internal/faults/inventory-latency")
    public Map<String, Object> reset() {
        requireDemoMode();
        boolean changed = faultState.setActive(false);
        log.info("event=demo_fault_reset dependency=inventory changed={}", changed);
        return status();
    }

    private void requireDemoMode() {
        if (!demoFaultsEnabled) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "demo fault control disabled");
        }
    }
}
