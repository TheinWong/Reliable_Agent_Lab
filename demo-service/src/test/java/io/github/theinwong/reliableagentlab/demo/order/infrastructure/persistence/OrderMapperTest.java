package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import static org.assertj.core.api.Assertions.assertThat;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import org.junit.jupiter.api.Test;

class OrderMapperTest {

    @Test
    void mapsDomainOrderToEntity() {
        Order order = new Order(1001L, 2001L, 2, OrderStatus.CREATED);

        OrderEntity entity = OrderMapper.toEntity(order);

        assertThat(entity.getId()).isEqualTo(1001L);
        assertThat(entity.getProductId()).isEqualTo(2001L);
        assertThat(entity.getQuantity()).isEqualTo(2);
        assertThat(entity.getStatus()).isEqualTo(OrderStatus.CREATED);
    }

    @Test
    void mapsEntityToDomainOrder() {
        OrderEntity entity = new OrderEntity(1001L, 2001L, 2, OrderStatus.CREATED);

        Order order = OrderMapper.toDomain(entity);

        assertThat(order).isEqualTo(new Order(1001L, 2001L, 2, OrderStatus.CREATED));
    }
}
