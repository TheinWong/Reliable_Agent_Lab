package dev.reliableagentlab.downstream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

class PaymentControllerTest {
    @Test
    void controlledHttpFailureIsRepeatableAndResettable() {
        PaymentController controller = new PaymentController(new FaultState(),
                new SimpleMeterRegistry(), true);
        assertThat(controller.authorizationPreview(1L).getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(controller.inject()).containsEntry("paymentHttp5xx", true);
        assertThat(controller.inject()).containsEntry("paymentHttp5xx", true);
        assertThat(controller.authorizationPreview(1L).getStatusCode())
                .isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(controller.reset()).containsEntry("paymentHttp5xx", false);
        assertThat(controller.reset()).containsEntry("paymentHttp5xx", false);
        assertThat(controller.authorizationPreview(1L).getStatusCode()).isEqualTo(HttpStatus.OK);
    }

    @Test
    void mutationIsUnavailableOutsideDemoMode() {
        PaymentController controller = new PaymentController(new FaultState(),
                new SimpleMeterRegistry(), false);
        assertThatThrownBy(controller::inject).isInstanceOf(ResponseStatusException.class);
    }
}
