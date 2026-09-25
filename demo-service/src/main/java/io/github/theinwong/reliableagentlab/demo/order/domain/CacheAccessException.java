package io.github.theinwong.reliableagentlab.demo.order.domain;

public class CacheAccessException extends RuntimeException {

    public CacheAccessException(String message, Throwable cause) {
        super(message, cause);
    }
}
