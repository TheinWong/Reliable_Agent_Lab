package io.github.theinwong.reliableagentlab.demo.order.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import io.github.theinwong.reliableagentlab.demo.order.domain.CacheAccessException;
import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderCache;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderRepository;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class OrderServiceTest {

    private static final long ORDER_ID = 1001L;

    private OrderRepository orderRepository;
    private OrderCache orderCache;
    private SimpleMeterRegistry meterRegistry;
    private OrderService orderService;

    @BeforeEach
    void setUp() {
        orderRepository = mock(OrderRepository.class);
        orderCache = mock(OrderCache.class);
        meterRegistry = new SimpleMeterRegistry();
        orderService = new OrderService(orderRepository, orderCache, new OrderMetrics(meterRegistry));
    }

    @Test
    void returnsOrderFromCacheWithoutReadingDatabase() {
        Order cachedOrder = existingOrder();
        when(orderCache.findById(ORDER_ID)).thenReturn(Optional.of(cachedOrder));

        Order result = orderService.findById(ORDER_ID);

        assertThat(result).isEqualTo(cachedOrder);
        assertCounter("order.cache.reads", "result", "hit", 1.0);
        verifyNoInteractions(orderRepository);
        verify(orderCache, never()).put(cachedOrder);
    }

    @Test
    void readsDatabaseAndPopulatesCacheAfterCacheMiss() {
        Order databaseOrder = existingOrder();
        when(orderCache.findById(ORDER_ID)).thenReturn(Optional.empty());
        when(orderRepository.findById(ORDER_ID)).thenReturn(Optional.of(databaseOrder));

        Order result = orderService.findById(ORDER_ID);

        assertThat(result).isEqualTo(databaseOrder);
        assertCounter("order.cache.reads", "result", "miss", 1.0);
        assertCounter("order.mysql.fallbacks", "reason", "cache_miss", 1.0);
        assertCounter("order.cache.writes", "result", "success", 1.0);
        verify(orderCache).put(databaseOrder);
    }

    @Test
    void fallsBackToDatabaseAndSkipsWriteAfterCacheReadFailure() {
        Order databaseOrder = existingOrder();
        when(orderCache.findById(ORDER_ID))
                .thenThrow(new CacheAccessException("Redis unavailable", new RuntimeException()));
        when(orderRepository.findById(ORDER_ID)).thenReturn(Optional.of(databaseOrder));

        Order result = orderService.findById(ORDER_ID);

        assertThat(result).isEqualTo(databaseOrder);
        assertCounter("order.cache.reads", "result", "error", 1.0);
        assertCounter("order.mysql.fallbacks", "reason", "cache_error", 1.0);
        assertCounter("order.cache.writes", "result", "skipped", 1.0);
        verify(orderCache, never()).put(databaseOrder);
    }

    @Test
    void returnsDatabaseOrderWhenCacheWriteFails() {
        Order databaseOrder = existingOrder();
        when(orderCache.findById(ORDER_ID)).thenReturn(Optional.empty());
        when(orderRepository.findById(ORDER_ID)).thenReturn(Optional.of(databaseOrder));
        doThrow(new CacheAccessException("Redis write failed", new RuntimeException()))
                .when(orderCache).put(databaseOrder);

        Order result = orderService.findById(ORDER_ID);

        assertThat(result).isEqualTo(databaseOrder);
        assertCounter("order.cache.writes", "result", "error", 1.0);
    }

    @Test
    void reportsNotFoundWhenDatabaseDoesNotContainOrder() {
        when(orderCache.findById(ORDER_ID)).thenReturn(Optional.empty());
        when(orderRepository.findById(ORDER_ID)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> orderService.findById(ORDER_ID))
                .isInstanceOf(OrderNotFoundException.class)
                .hasMessage("Order not found: " + ORDER_ID);
    }

    @Test
    void createsOrderInDatabaseWithoutWritingCache() {
        Order persistedOrder = existingOrder();
        when(orderRepository.save(Order.create(2001L, 2))).thenReturn(persistedOrder);

        Order result = orderService.create(2001L, 2);

        assertThat(result).isEqualTo(persistedOrder);
        verifyNoInteractions(orderCache);
    }

    private static Order existingOrder() {
        return new Order(ORDER_ID, 2001L, 2, OrderStatus.CREATED);
    }

    private void assertCounter(String name, String tagName, String tagValue, double expected) {
        assertThat(meterRegistry.get(name).tag(tagName, tagValue).counter().count())
                .isEqualTo(expected);
    }
}
