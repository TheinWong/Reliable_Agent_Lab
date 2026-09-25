package io.github.theinwong.reliableagentlab.demo.order.infrastructure.cache;

import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;

import java.time.Duration;
import org.junit.jupiter.api.Test;

class OrderCachePropertiesTest {

    @Test
    void rejectsMissingTtl() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new OrderCacheProperties(null))
                .withMessage("app.cache.order.ttl must be positive");
    }

    @Test
    void rejectsNonPositiveTtl() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new OrderCacheProperties(Duration.ZERO))
                .withMessage("app.cache.order.ttl must be positive");
    }
}
