package io.github.theinwong.reliableagentlab.demo.order.domain;

import java.util.Objects;

public record Order(
        Long id,
        long productId,
        int quantity,
        OrderStatus status) {

    public Order {
        if (productId <= 0) {
            throw new IllegalArgumentException("productId must be positive");
        }
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        Objects.requireNonNull(status, "status must not be null");
    }

    public static Order create(long productId, int quantity) {
        return new Order(null, productId, quantity, OrderStatus.CREATED);
    }
}
