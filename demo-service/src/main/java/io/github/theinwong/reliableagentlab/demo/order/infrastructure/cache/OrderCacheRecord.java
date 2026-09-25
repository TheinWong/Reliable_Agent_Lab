package io.github.theinwong.reliableagentlab.demo.order.infrastructure.cache;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;

record OrderCacheRecord(
        Long id,
        long productId,
        int quantity,
        OrderStatus status) {

    static OrderCacheRecord from(Order order) {
        return new OrderCacheRecord(
                order.id(),
                order.productId(),
                order.quantity(),
                order.status());
    }

    Order toDomain() {
        return new Order(id, productId, quantity, status);
    }
}
