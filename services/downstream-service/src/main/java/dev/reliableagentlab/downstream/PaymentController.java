package dev.reliableagentlab.downstream;

import java.util.Map;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@ConditionalOnProperty(name = "app.role", havingValue = "payment")
public class PaymentController {
    private static final Logger log = LoggerFactory.getLogger(PaymentController.class);
    private final FaultState faultState;
    private final Counter errors;
    private final boolean demoFaultsEnabled;

    public PaymentController(FaultState faultState, MeterRegistry registry,
            @Value("${app.fault-injection.enabled:false}") boolean demoFaultsEnabled) {
        this.faultState = faultState;
        this.errors = registry.counter("payment.preview.requests", "result", "error");
        this.demoFaultsEnabled = demoFaultsEnabled;
    }

    @GetMapping("/api/payments/authorization-preview")
    public ResponseEntity<Map<String, Object>> authorizationPreview(@RequestParam long orderId) {
        if (faultState.isActive()) {
            errors.increment();
            log.warn("event=payment_http_5xx_injected orderId={}", orderId);
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(
                    Map.of("code", "DEMO_PAYMENT_5XX", "orderId", orderId));
        }
        return ResponseEntity.ok(Map.of("orderId", orderId, "authorized", true));
    }

    @GetMapping("/internal/faults")
    public Map<String, Object> status() {
        return Map.of("paymentHttp5xx", faultState.isActive(),
                "faultStartedAt", faultState.activatedAt());
    }

    @PutMapping("/internal/faults/payment-5xx")
    public Map<String, Object> inject() {
        requireDemoMode();
        boolean changed = faultState.setActive(true);
        log.warn("event=demo_fault_injected dependency=payment mode=http_5xx changed={}", changed);
        return status();
    }

    @DeleteMapping("/internal/faults/payment-5xx")
    public Map<String, Object> reset() {
        requireDemoMode();
        boolean changed = faultState.setActive(false);
        log.info("event=demo_fault_reset dependency=payment changed={}", changed);
        return status();
    }

    private void requireDemoMode() {
        if (!demoFaultsEnabled) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "demo fault control disabled");
        }
    }
}
