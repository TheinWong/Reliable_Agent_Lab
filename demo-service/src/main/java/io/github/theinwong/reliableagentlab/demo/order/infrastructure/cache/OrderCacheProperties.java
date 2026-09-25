package io.github.theinwong.reliableagentlab.demo.order.infrastructure.cache;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("app.cache.order")
public record OrderCacheProperties(Duration ttl) {

    public OrderCacheProperties {
        if (ttl == null || ttl.isZero() || ttl.isNegative()) {
            throw new IllegalArgumentException("app.cache.order.ttl must be positive");
        }
    }
}
