package dev.reliableagentlab.order;

import java.time.Duration;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class OrderQueryService {
    private static final Logger log = LoggerFactory.getLogger(OrderQueryService.class);

    private final OrderRepository repository;
    private final StringRedisTemplate redis;
    private final ObjectMapper objectMapper;
    private final FaultState faultState;
    private final DemoEventRecorder eventRecorder;
    private final Duration cacheTtl;
    private final Counter cacheHits;
    private final Counter cacheMisses;
    private final Counter cacheErrors;
    private final Counter mysqlFallbacks;
    private final Counter mysqlControlledFailures;

    public OrderQueryService(
            OrderRepository repository,
            StringRedisTemplate redis,
            ObjectMapper objectMapper,
            FaultState faultState,
            DemoEventRecorder eventRecorder,
            MeterRegistry meterRegistry,
            @Value("${app.cache.ttl:5m}") Duration cacheTtl) {
        this.repository = repository;
        this.redis = redis;
        this.objectMapper = objectMapper;
        this.faultState = faultState;
        this.eventRecorder = eventRecorder;
        this.cacheTtl = cacheTtl;
        this.cacheHits = meterRegistry.counter("order.cache.reads", "result", "hit");
        this.cacheMisses = meterRegistry.counter("order.cache.reads", "result", "miss");
        this.cacheErrors = meterRegistry.counter("order.cache.reads", "result", "error");
        this.mysqlFallbacks = meterRegistry.counter("order.mysql.fallbacks", "reason", "cache_error");
        this.mysqlControlledFailures = meterRegistry.counter("order.mysql.failures", "reason", "controlled_unavailable");
    }

    public OrderResponse findById(long id) {
        String key = "order:" + id;
        boolean cacheReadFailed = false;
        try {
            if (faultState.isRedisUnavailable()) {
                throw new IllegalStateException("controlled Redis unavailability is active");
            }
            String cached = redis.opsForValue().get(key);
            if (cached != null) {
                cacheHits.increment();
                return objectMapper.readValue(cached, OrderResponse.class).withSource("CACHE", false);
            }
            cacheMisses.increment();
        } catch (RuntimeException | JsonProcessingException exception) {
            cacheReadFailed = true;
            cacheErrors.increment();
            mysqlFallbacks.increment();
            log.warn("event=order_cache_read_failed orderId={} action=mysql_fallback reason={}",
                    id, exception.getClass().getSimpleName());
            eventRecorder.record("order_cache_read_failed", "redis", exception.getClass().getSimpleName());
        }

        if (faultState.isMysqlUnavailable()) {
            mysqlControlledFailures.increment();
            log.warn("event=order_mysql_read_failed orderId={} reason=controlled_unavailable", id);
            eventRecorder.record("order_mysql_read_failed", "mysql", "controlled_unavailable");
            throw new DemoMysqlUnavailableException();
        }
        OrderEntity order = repository.findById(id).orElseThrow(() -> new OrderNotFoundException(id));
        OrderResponse response = OrderResponse.from(order, "DATABASE", cacheReadFailed);
        if (!cacheReadFailed) {
            try {
                redis.opsForValue().set(key, objectMapper.writeValueAsString(response), cacheTtl);
            } catch (RuntimeException | JsonProcessingException exception) {
                log.warn("event=order_cache_write_failed orderId={} action=return_database_result reason={}",
                        id, exception.getClass().getSimpleName());
                eventRecorder.record("order_cache_write_failed", "redis", exception.getClass().getSimpleName());
            }
        }
        return response;
    }
}
