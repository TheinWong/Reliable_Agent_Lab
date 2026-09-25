package io.github.theinwong.reliableagentlab.demo.order.application;

public class OrderNotFoundException extends RuntimeException {

    public OrderNotFoundException(long orderId) {
        super("Order not found: " + orderId);
    }
}
