package io.github.theinwong.reliableagentlab.demo.order.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;

import org.junit.jupiter.api.Test;

class OrderTest {

    @Test
    void createsANewOrderWithCreatedStatus() {
        Order order = Order.create(2001L, 2);

        assertThat(order.id()).isNull();
        assertThat(order.productId()).isEqualTo(2001L);
        assertThat(order.quantity()).isEqualTo(2);
        assertThat(order.status()).isEqualTo(OrderStatus.CREATED);
    }

    @Test
    void rejectsNonPositiveProductId() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> Order.create(0L, 2))
                .withMessage("productId must be positive");
    }

    @Test
    void rejectsNonPositiveQuantity() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> Order.create(2001L, 0))
                .withMessage("quantity must be positive");
    }
}
