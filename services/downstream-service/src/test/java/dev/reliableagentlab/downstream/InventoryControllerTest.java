package dev.reliableagentlab.downstream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

class InventoryControllerTest {
    @Test
    void latencyFaultIsRepeatableAndResettable() throws InterruptedException {
        InventoryController controller = new InventoryController(new FaultState(),
                new SimpleMeterRegistry(), true);
        assertThat(controller.availability("sku-1").getBody()).containsEntry("available", true);
        assertThat(controller.inject()).containsEntry("inventoryLatency", true);
        assertThat(controller.inject()).containsEntry("inventoryLatency", true);
        long start = System.nanoTime();
        controller.availability("sku-1");
        long elapsedMillis = (System.nanoTime() - start) / 1_000_000;
        assertThat(elapsedMillis).isGreaterThanOrEqualTo(750);
        assertThat(controller.reset()).containsEntry("inventoryLatency", false);
        assertThat(controller.reset()).containsEntry("inventoryLatency", false);
    }

    @Test
    void mutationIsUnavailableOutsideDemoMode() {
        InventoryController controller = new InventoryController(new FaultState(),
                new SimpleMeterRegistry(), false);
        assertThatThrownBy(controller::inject).isInstanceOf(ResponseStatusException.class);
    }
}
