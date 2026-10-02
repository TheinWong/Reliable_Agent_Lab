package dev.reliableagentlab.order;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class CheckoutPreviewServiceTest {
    @Test
    void previewCallsBothIndependentDownstreamServices() {
        RestClient.Builder inventoryBuilder = RestClient.builder().baseUrl("http://inventory");
        RestClient.Builder paymentBuilder = RestClient.builder().baseUrl("http://payment");
        MockRestServiceServer inventory = MockRestServiceServer.bindTo(inventoryBuilder).build();
        MockRestServiceServer payment = MockRestServiceServer.bindTo(paymentBuilder).build();
        inventory.expect(once(), requestTo("http://inventory/api/inventory/sku-1"))
                .andRespond(withSuccess("{\"sku\":\"sku-1\",\"available\":true}", MediaType.APPLICATION_JSON));
        payment.expect(once(), requestTo("http://payment/api/payments/authorization-preview?orderId=1"))
                .andRespond(withSuccess("{\"orderId\":1,\"authorized\":true}", MediaType.APPLICATION_JSON));
        OrderQueryService orders = org.mockito.Mockito.mock(OrderQueryService.class);
        CheckoutPreviewService service = new CheckoutPreviewService(
                orders, new DemoEventRecorder(), new SimpleMeterRegistry(),
                inventoryBuilder.build(), paymentBuilder.build());

        CheckoutPreviewResponse result = service.preview(1L);

        assertThat(result.status()).isEqualTo("OK");
        assertThat(result.inventoryAvailable()).isTrue();
        assertThat(result.paymentAuthorized()).isTrue();
        org.mockito.Mockito.verify(orders).findById(1L);
        inventory.verify();
        payment.verify();
    }

    @Test
    void paymentHttpFailureIsExplicitAndRecorded() {
        RestClient.Builder inventoryBuilder = RestClient.builder().baseUrl("http://inventory");
        RestClient.Builder paymentBuilder = RestClient.builder().baseUrl("http://payment");
        MockRestServiceServer inventory = MockRestServiceServer.bindTo(inventoryBuilder).build();
        MockRestServiceServer payment = MockRestServiceServer.bindTo(paymentBuilder).build();
        inventory.expect(once(), requestTo("http://inventory/api/inventory/sku-1"))
                .andRespond(withSuccess("{\"sku\":\"sku-1\",\"available\":true}", MediaType.APPLICATION_JSON));
        payment.expect(once(), requestTo("http://payment/api/payments/authorization-preview?orderId=1"))
                .andRespond(withServerError());
        DemoEventRecorder events = new DemoEventRecorder();
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        CheckoutPreviewService service = new CheckoutPreviewService(
                org.mockito.Mockito.mock(OrderQueryService.class), events, registry,
                inventoryBuilder.build(), paymentBuilder.build());

        assertThatThrownBy(() -> service.preview(1L))
                .isInstanceOf(DownstreamFailureException.class)
                .hasMessage("PAYMENT_UNAVAILABLE");
        assertThat(events.recent()).anyMatch(event -> event.type().equals("order_payment_request_failed"));
        assertThat(registry.find("order.payment.requests").tag("result", "error").counter().count())
                .isEqualTo(1.0);
        inventory.verify();
        payment.verify();
    }
}
