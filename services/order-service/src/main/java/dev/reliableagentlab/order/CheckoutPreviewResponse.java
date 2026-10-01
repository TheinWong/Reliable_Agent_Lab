package dev.reliableagentlab.order;

public record CheckoutPreviewResponse(
        long orderId,
        String status,
        long inventoryLatencyMs,
        boolean inventoryAvailable,
        boolean paymentAuthorized) {
}
