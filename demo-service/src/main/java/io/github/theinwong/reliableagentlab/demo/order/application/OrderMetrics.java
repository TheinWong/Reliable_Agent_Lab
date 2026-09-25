package io.github.theinwong.reliableagentlab.demo.order.application;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Component;

@Component
public class OrderMetrics {

    private static final String CACHE_READS = "order.cache.reads";
    private static final String MYSQL_FALLBACKS = "order.mysql.fallbacks";
    private static final String CACHE_WRITES = "order.cache.writes";

    private final Counter cacheReadHit;
    private final Counter cacheReadMiss;
    private final Counter cacheReadError;
    private final Counter mysqlFallbackCacheMiss;
    private final Counter mysqlFallbackCacheError;
    private final Counter cacheWriteSuccess;
    private final Counter cacheWriteError;
    private final Counter cacheWriteSkipped;

    public OrderMetrics(MeterRegistry registry) {
        cacheReadHit = counter(registry, CACHE_READS, "result", "hit", "Order cache read outcomes");
        cacheReadMiss = counter(registry, CACHE_READS, "result", "miss", "Order cache read outcomes");
        cacheReadError = counter(registry, CACHE_READS, "result", "error", "Order cache read outcomes");
        mysqlFallbackCacheMiss = counter(
                registry, MYSQL_FALLBACKS, "reason", "cache_miss", "Order MySQL fallback reasons");
        mysqlFallbackCacheError = counter(
                registry, MYSQL_FALLBACKS, "reason", "cache_error", "Order MySQL fallback reasons");
        cacheWriteSuccess = counter(registry, CACHE_WRITES, "result", "success", "Order cache write outcomes");
        cacheWriteError = counter(registry, CACHE_WRITES, "result", "error", "Order cache write outcomes");
        cacheWriteSkipped = counter(registry, CACHE_WRITES, "result", "skipped", "Order cache write outcomes");
    }

    public void cacheReadHit() {
        cacheReadHit.increment();
    }

    public void cacheReadMiss() {
        cacheReadMiss.increment();
    }

    public void cacheReadError() {
        cacheReadError.increment();
    }

    public void mysqlFallbackCacheMiss() {
        mysqlFallbackCacheMiss.increment();
    }

    public void mysqlFallbackCacheError() {
        mysqlFallbackCacheError.increment();
    }

    public void cacheWriteSuccess() {
        cacheWriteSuccess.increment();
    }

    public void cacheWriteError() {
        cacheWriteError.increment();
    }

    public void cacheWriteSkipped() {
        cacheWriteSkipped.increment();
    }

    private static Counter counter(
            MeterRegistry registry, String name, String tagName, String tagValue, String description) {
        return Counter.builder(name)
                .description(description)
                .tag(tagName, tagValue)
                .register(registry);
    }
}
