package io.github.theinwong.reliableagentlab.demo.order.api.dto;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;

public record OrderResponse(
        Long id,
        long productId,
        int quantity,
        OrderStatus status) {

    public static OrderResponse from(Order order) {
        return new OrderResponse(
                order.id(),
                order.productId(),
                order.quantity(),
                order.status());
    }
}
