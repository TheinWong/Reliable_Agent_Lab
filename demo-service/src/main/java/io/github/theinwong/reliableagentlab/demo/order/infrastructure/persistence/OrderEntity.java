package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "orders")
class OrderEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "product_id", nullable = false)
    private long productId;

    @Column(nullable = false)
    private int quantity;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private OrderStatus status;

    protected OrderEntity() {
    }

    OrderEntity(Long id, long productId, int quantity, OrderStatus status) {
        this.id = id;
        this.productId = productId;
        this.quantity = quantity;
        this.status = status;
    }

    Long getId() {
        return id;
    }

    long getProductId() {
        return productId;
    }

    int getQuantity() {
        return quantity;
    }

    OrderStatus getStatus() {
        return status;
    }
}
