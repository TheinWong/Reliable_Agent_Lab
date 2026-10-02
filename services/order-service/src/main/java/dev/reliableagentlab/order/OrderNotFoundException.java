package dev.reliableagentlab.order;

public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(long id) {
        super("order not found: " + id);
    }
}
