package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;

final class OrderMapper {

    private OrderMapper() {
    }

    static OrderEntity toEntity(Order order) {
        return new OrderEntity(
                order.id(),
                order.productId(),
                order.quantity(),
                order.status());
    }

    static Order toDomain(OrderEntity entity) {
        return new Order(
                entity.getId(),
                entity.getProductId(),
                entity.getQuantity(),
                entity.getStatus());
    }
}
