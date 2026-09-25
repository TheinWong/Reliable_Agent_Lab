package io.github.theinwong.reliableagentlab.demo.order.infrastructure.cache;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.theinwong.reliableagentlab.demo.order.domain.CacheAccessException;
import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderCache;
import java.util.Optional;
import org.springframework.dao.DataAccessException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class RedisOrderCache implements OrderCache {

    private static final String KEY_PREFIX = "order:";

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final OrderCacheProperties properties;

    public RedisOrderCache(
            StringRedisTemplate redisTemplate,
            ObjectMapper objectMapper,
            OrderCacheProperties properties) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    @Override
    public Optional<Order> findById(long orderId) {
        try {
            String value = redisTemplate.opsForValue().get(key(orderId));
            if (value == null) {
                return Optional.empty();
            }

            return Optional.of(objectMapper.readValue(value, OrderCacheRecord.class).toDomain());
        } catch (DataAccessException | JsonProcessingException exception) {
            throw new CacheAccessException("Failed to read order from Redis", exception);
        }
    }

    @Override
    public void put(Order order) {
        if (order.id() == null) {
            throw new IllegalArgumentException("Cannot cache an order without an id");
        }

        try {
            String value = objectMapper.writeValueAsString(OrderCacheRecord.from(order));
            redisTemplate.opsForValue().set(key(order.id()), value, properties.ttl());
        } catch (DataAccessException | JsonProcessingException exception) {
            throw new CacheAccessException("Failed to write order to Redis", exception);
        }
    }

    private static String key(long orderId) {
        return KEY_PREFIX + orderId;
    }
}
