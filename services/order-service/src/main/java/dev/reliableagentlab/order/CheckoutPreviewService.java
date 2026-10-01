package dev.reliableagentlab.order;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
public class CheckoutPreviewService {
    private static final Logger log = LoggerFactory.getLogger(CheckoutPreviewService.class);
    private static final long SLOW_INVENTORY_THRESHOLD_MS = 500;
    private final OrderQueryService orders;
    private final RestClient inventory;
    private final RestClient payment;
    private final DemoEventRecorder events;
    private final Counter inventorySlow;
    private final Counter inventoryErrors;
    private final Counter paymentErrors;

    @Autowired
    public CheckoutPreviewService(
            OrderQueryService orders,
            DemoEventRecorder events,
            MeterRegistry registry,
            @Value("${app.inventory-url:http://localhost:18081}") String inventoryUrl,
            @Value("${app.payment-url:http://localhost:18082}") String paymentUrl) {
        this(orders, events, registry, client(inventoryUrl), client(paymentUrl));
    }

    CheckoutPreviewService(OrderQueryService orders, DemoEventRecorder events,
            MeterRegistry registry, RestClient inventory, RestClient payment) {
        this.orders = orders;
        this.events = events;
        this.inventory = inventory;
        this.payment = payment;
        this.inventorySlow = registry.counter("order.inventory.requests", "result", "slow");
        this.inventoryErrors = registry.counter("order.inventory.requests", "result", "error");
        this.paymentErrors = registry.counter("order.payment.requests", "result", "error");
    }

    private static RestClient client(String baseUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(1));
        factory.setReadTimeout(Duration.ofSeconds(2));
        return RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public CheckoutPreviewResponse preview(long orderId) {
        orders.findById(orderId);
        InventoryAvailability inventoryResult;
        long start = System.nanoTime();
        try {
            inventoryResult = inventory.get().uri("/api/inventory/sku-1")
                    .retrieve().body(InventoryAvailability.class);
            if (inventoryResult == null || !inventoryResult.available()) {
                throw new IllegalStateException("inventory response was empty or unavailable");
            }
        } catch (RestClientException | IllegalStateException exception) {
            inventoryErrors.increment();
            log.warn("event=order_inventory_request_failed orderId={} reason={}",
                    orderId, exception.getClass().getSimpleName());
            events.record("order_inventory_request_failed", "inventory", exception.getClass().getSimpleName());
            throw new DownstreamFailureException("INVENTORY_UNAVAILABLE", exception);
        }
        long inventoryLatencyMs = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start);
        if (inventoryLatencyMs >= SLOW_INVENTORY_THRESHOLD_MS) {
            inventorySlow.increment();
            log.warn("event=order_inventory_slow orderId={} latencyMs={}", orderId, inventoryLatencyMs);
            events.record("order_inventory_slow", "inventory", Long.toString(inventoryLatencyMs));
        }

        PaymentPreview paymentResult;
        try {
            paymentResult = payment.get()
                    .uri(builder -> builder.path("/api/payments/authorization-preview")
                            .queryParam("orderId", orderId).build())
                    .retrieve().body(PaymentPreview.class);
            if (paymentResult == null || !paymentResult.authorized()) {
                throw new IllegalStateException("payment response was empty or denied");
            }
        } catch (RestClientException | IllegalStateException exception) {
            paymentErrors.increment();
            log.warn("event=order_payment_request_failed orderId={} reason={}",
                    orderId, exception.getClass().getSimpleName());
            events.record("order_payment_request_failed", "payment", exception.getClass().getSimpleName());
            throw new DownstreamFailureException("PAYMENT_UNAVAILABLE", exception);
        }
        return new CheckoutPreviewResponse(orderId, "OK", inventoryLatencyMs, true, true);
    }

    private record InventoryAvailability(String sku, boolean available) {
    }

    private record PaymentPreview(long orderId, boolean authorized) {
    }
}
