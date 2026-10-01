package dev.reliableagentlab.order;

import static org.assertj.core.api.Assertions.assertThat;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;

class DemoEvidenceControllerTest {
    @Test
    void readOnlyEvidenceReflectsFaultAndBoundedEvents() {
        FaultState faultState = new FaultState();
        DemoEventRecorder recorder = new DemoEventRecorder();
        SimpleMeterRegistry meters = new SimpleMeterRegistry();
        DemoEvidenceController controller = new DemoEvidenceController(faultState, recorder, meters);

        faultState.setRedisUnavailable(true);
        faultState.setMysqlUnavailable(true);
        recorder.record("demo_fault_injected", "redis", "unavailable");
        meters.counter("order.cache.reads", "result", "error").increment();

        assertThat(controller.metrics()).containsEntry("redisUnavailable", true);
        assertThat(controller.metrics()).containsEntry("mysqlUnavailable", true);
        assertThat(controller.metrics()).containsEntry("cacheReadErrors", 1.0);
        assertThat(controller.logs().get("events")).hasSize(1);
        assertThat(controller.logs().get("events").getFirst().type()).isEqualTo("demo_fault_injected");
    }

    @Test
    void eventBufferHasFixedMaximum() {
        DemoEventRecorder recorder = new DemoEventRecorder();
        for (int index = 0; index < 120; index++) {
            recorder.record("event", "redis", Integer.toString(index));
        }
        assertThat(recorder.recent()).hasSize(100);
        assertThat(recorder.recent().getFirst().detail()).isEqualTo("20");
    }
}
