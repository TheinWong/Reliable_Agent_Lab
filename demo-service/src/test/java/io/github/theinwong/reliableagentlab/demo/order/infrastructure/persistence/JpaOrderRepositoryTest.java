package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class JpaOrderRepositoryTest {

    private SpringDataOrderJpaRepository springDataRepository;
    private JpaOrderRepository orderRepository;

    @BeforeEach
    void setUp() {
        springDataRepository = mock(SpringDataOrderJpaRepository.class);
        orderRepository = new JpaOrderRepository(springDataRepository);
    }

    @Test
    void savesAndReturnsDomainOrder() {
        Order newOrder = Order.create(2001L, 2);
        when(springDataRepository.save(any(OrderEntity.class)))
                .thenReturn(new OrderEntity(1001L, 2001L, 2, OrderStatus.CREATED));

        Order savedOrder = orderRepository.save(newOrder);

        assertThat(savedOrder).isEqualTo(
                new Order(1001L, 2001L, 2, OrderStatus.CREATED));
        verify(springDataRepository).save(any(OrderEntity.class));
    }

    @Test
    void findsAndMapsExistingOrder() {
        when(springDataRepository.findById(1001L))
                .thenReturn(Optional.of(
                        new OrderEntity(1001L, 2001L, 2, OrderStatus.CREATED)));

        Optional<Order> order = orderRepository.findById(1001L);

        assertThat(order).contains(
                new Order(1001L, 2001L, 2, OrderStatus.CREATED));
    }

    @Test
    void returnsEmptyWhenOrderDoesNotExist() {
        when(springDataRepository.findById(1001L)).thenReturn(Optional.empty());

        Optional<Order> order = orderRepository.findById(1001L);

        assertThat(order).isEmpty();
    }
}
