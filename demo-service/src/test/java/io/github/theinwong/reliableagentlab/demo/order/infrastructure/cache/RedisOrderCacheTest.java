package io.github.theinwong.reliableagentlab.demo.order.infrastructure.cache;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.theinwong.reliableagentlab.demo.order.domain.CacheAccessException;
import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

class RedisOrderCacheTest {

    private static final Duration TTL = Duration.ofMinutes(5);

    private StringRedisTemplate redisTemplate;
    private ValueOperations<String, String> valueOperations;
    private RedisOrderCache orderCache;

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        redisTemplate = mock(StringRedisTemplate.class);
        valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        orderCache = new RedisOrderCache(
                redisTemplate,
                new ObjectMapper().findAndRegisterModules(),
                new OrderCacheProperties(TTL));
    }

    @Test
    void returnsCachedOrder() {
        when(valueOperations.get("order:1001"))
                .thenReturn("""
                        {"id":1001,"productId":2001,"quantity":2,"status":"CREATED"}
                        """);

        Optional<Order> order = orderCache.findById(1001L);

        assertThat(order).contains(
                new Order(1001L, 2001L, 2, OrderStatus.CREATED));
    }

    @Test
    void returnsEmptyOnCacheMiss() {
        when(valueOperations.get("order:1001")).thenReturn(null);

        Optional<Order> order = orderCache.findById(1001L);

        assertThat(order).isEmpty();
    }

    @Test
    void translatesRedisConnectionFailure() {
        when(valueOperations.get("order:1001"))
                .thenThrow(new RedisConnectionFailureException("Redis unavailable"));

        assertThatThrownBy(() -> orderCache.findById(1001L))
                .isInstanceOf(CacheAccessException.class)
                .hasMessage("Failed to read order from Redis");
    }

    @Test
    void translatesInvalidCachedJson() {
        when(valueOperations.get("order:1001")).thenReturn("not-json");

        assertThatThrownBy(() -> orderCache.findById(1001L))
                .isInstanceOf(CacheAccessException.class)
                .hasMessage("Failed to read order from Redis");
    }

    @Test
    void writesOrderAsJsonWithTtl() throws Exception {
        Order order = new Order(1001L, 2001L, 2, OrderStatus.CREATED);

        orderCache.put(order);

        verify(valueOperations).set(
                "order:1001",
                "{\"id\":1001,\"productId\":2001,\"quantity\":2,\"status\":\"CREATED\"}",
                TTL);
    }

    @Test
    void rejectsOrderWithoutId() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> orderCache.put(Order.create(2001L, 2)))
                .withMessage("Cannot cache an order without an id");
    }
}
