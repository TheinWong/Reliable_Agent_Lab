package dev.reliableagentlab.order;

public class DemoMysqlUnavailableException extends RuntimeException {
    public DemoMysqlUnavailableException() {
        super("controlled MySQL connection failure is active");
    }
}
