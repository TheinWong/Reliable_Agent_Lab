package io.github.theinwong.reliableagentlab.demo.order.domain;

import java.util.Optional;

public interface OrderCache {

    Optional<Order> findById(long orderId);

    void put(Order order);
}
