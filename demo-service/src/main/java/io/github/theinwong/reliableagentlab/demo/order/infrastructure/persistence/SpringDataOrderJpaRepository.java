package io.github.theinwong.reliableagentlab.demo.order.infrastructure.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

interface SpringDataOrderJpaRepository extends JpaRepository<OrderEntity, Long> {
}
