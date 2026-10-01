package dev.reliableagentlab.order;

import java.math.BigDecimal;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "orders")
public class OrderEntity {
    @Id
    private Long id;
    private String customerId;
    private BigDecimal total;
    private String status;

    protected OrderEntity() {
    }

    public OrderEntity(Long id, String customerId, BigDecimal total, String status) {
        this.id = id;
        this.customerId = customerId;
        this.total = total;
        this.status = status;
    }

    public Long getId() {
        return id;
    }

    public String getCustomerId() {
        return customerId;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public String getStatus() {
        return status;
    }
}
