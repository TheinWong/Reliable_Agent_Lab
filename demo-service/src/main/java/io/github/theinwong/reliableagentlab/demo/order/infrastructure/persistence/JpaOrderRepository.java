package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class JpaOrderRepository implements OrderRepository {

    private final SpringDataOrderJpaRepository repository;

    public JpaOrderRepository(SpringDataOrderJpaRepository repository) {
        this.repository = repository;
    }

    @Override
    public Order save(Order order) {
        OrderEntity savedEntity = repository.save(OrderMapper.toEntity(order));
        return OrderMapper.toDomain(savedEntity);
    }

    @Override
    public Optional<Order> findById(long orderId) {
        return repository.findById(orderId).map(OrderMapper::toDomain);
    }
}
