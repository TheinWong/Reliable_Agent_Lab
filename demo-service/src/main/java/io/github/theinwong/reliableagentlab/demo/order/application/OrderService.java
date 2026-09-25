package io.github.theinwong.reliableagentlab.demo.order.application;

import io.github.theinwong.reliableagentlab.demo.order.domain.CacheAccessException;
import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderCache;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class OrderService {

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository orderRepository;
    private final OrderCache orderCache;
    private final OrderMetrics orderMetrics;

    public OrderService(OrderRepository orderRepository, OrderCache orderCache, OrderMetrics orderMetrics) {
        this.orderRepository = orderRepository;
        this.orderCache = orderCache;
        this.orderMetrics = orderMetrics;
    }

    public Order create(long productId, int quantity) {
        return orderRepository.save(Order.create(productId, quantity));
    }

    public Order findById(long orderId) {
        boolean cacheAvailable = true;

        try {
            var cachedOrder = orderCache.findById(orderId);
            if (cachedOrder.isPresent()) {
                orderMetrics.cacheReadHit();
                return cachedOrder.get();
            }
            orderMetrics.cacheReadMiss();
            orderMetrics.mysqlFallbackCacheMiss();
        } catch (CacheAccessException exception) {
            cacheAvailable = false;
            orderMetrics.cacheReadError();
            orderMetrics.mysqlFallbackCacheError();
            LOGGER.warn(
                    "event=order_cache_read_failed orderId={} action=mysql_fallback",
                    orderId,
                    exception);
        }

        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));

        if (cacheAvailable) {
            try {
                orderCache.put(order);
                orderMetrics.cacheWriteSuccess();
            } catch (CacheAccessException exception) {
                orderMetrics.cacheWriteError();
                LOGGER.warn(
                        "event=order_cache_write_failed orderId={} action=return_database_result",
                        orderId,
                        exception);
            }
        } else {
            orderMetrics.cacheWriteSkipped();
        }

        return order;
    }
}
