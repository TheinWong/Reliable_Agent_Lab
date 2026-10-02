package dev.reliableagentlab.order;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.Optional;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

@ExtendWith(MockitoExtension.class)
class OrderQueryServiceTest {
    @Mock
    private OrderRepository repository;
    @Mock
    private StringRedisTemplate redis;
    @Mock
    private ValueOperations<String, String> values;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final FaultState faultState = new FaultState();
    private OrderQueryService service;

    @BeforeEach
    void setUp() {
        service = new OrderQueryService(
                repository, redis, objectMapper, faultState, new DemoEventRecorder(),
                new SimpleMeterRegistry(), Duration.ofMinutes(5));
    }

    @Test
    void cacheMissReadsMysqlAndPopulatesCache() {
        OrderEntity order = new OrderEntity(1L, "customer", new BigDecimal("12.50"), "CONFIRMED");
        when(redis.opsForValue()).thenReturn(values);
        when(values.get("order:1")).thenReturn(null);
        when(repository.findById(1L)).thenReturn(Optional.of(order));

        OrderResponse response = service.findById(1L);

        assertThat(response.source()).isEqualTo("DATABASE");
        assertThat(response.cacheDegraded()).isFalse();
        verify(values).set(org.mockito.ArgumentMatchers.eq("order:1"),
                org.mockito.ArgumentMatchers.anyString(), org.mockito.ArgumentMatchers.eq(Duration.ofMinutes(5)));
    }

    @Test
    void controlledRedisFailureFallsBackToMysqlAndSkipsCacheWrite() {
        faultState.setRedisUnavailable(true);
        OrderEntity order = new OrderEntity(1L, "customer", new BigDecimal("12.50"), "CONFIRMED");
        when(repository.findById(1L)).thenReturn(Optional.of(order));

        OrderResponse response = service.findById(1L);

        assertThat(response.source()).isEqualTo("DATABASE");
        assertThat(response.cacheDegraded()).isTrue();
        verify(redis, never()).opsForValue();
    }

    @Test
    void controlledMysqlFailureReturnsExplicitFailureWithoutRepositoryRead() {
        faultState.setMysqlUnavailable(true);
        when(redis.opsForValue()).thenReturn(values);
        when(values.get("order:1")).thenReturn(null);

        assertThatThrownBy(() -> service.findById(1L))
                .isInstanceOf(DemoMysqlUnavailableException.class);

        verify(repository, never()).findById(1L);
    }
}
