package dev.reliableagentlab.order;

import java.math.BigDecimal;

public record OrderResponse(
        Long id,
        String customerId,
        BigDecimal total,
        String status,
        String source,
        boolean cacheDegraded) {

    static OrderResponse from(OrderEntity order, String source, boolean cacheDegraded) {
        return new OrderResponse(
                order.getId(), order.getCustomerId(), order.getTotal(), order.getStatus(), source, cacheDegraded);
    }

    OrderResponse withSource(String newSource, boolean degraded) {
        return new OrderResponse(id, customerId, total, status, newSource, degraded);
    }
}
