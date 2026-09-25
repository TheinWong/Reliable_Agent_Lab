package io.github.theinwong.reliableagentlab.demo.order.domain;

import java.util.Optional;

public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findById(long orderId);
}
