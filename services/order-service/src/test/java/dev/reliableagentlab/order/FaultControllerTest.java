package dev.reliableagentlab.order;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class FaultControllerTest {
    @Test
    void injectAndResetAreIdempotent() {
        FaultController controller = new FaultController(new FaultState(), new DemoEventRecorder());

        assertThat(controller.injectRedisUnavailable()).containsEntry("redisUnavailable", true);
        assertThat(controller.injectRedisUnavailable()).containsEntry("redisUnavailable", true);
        assertThat(controller.resetRedisUnavailable()).containsEntry("redisUnavailable", false);
        assertThat(controller.resetRedisUnavailable()).containsEntry("redisUnavailable", false);
        assertThat(controller.injectMysqlUnavailable()).containsEntry("mysqlUnavailable", true);
        assertThat(controller.injectMysqlUnavailable()).containsEntry("mysqlUnavailable", true);
        assertThat(controller.resetMysqlUnavailable()).containsEntry("mysqlUnavailable", false);
        assertThat(controller.resetMysqlUnavailable()).containsEntry("mysqlUnavailable", false);
    }
}
