package dev.reliableagentlab.order;

import java.math.BigDecimal;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class OrderServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }

    @Bean
    CommandLineRunner seedOrder(OrderRepository repository) {
        return args -> repository.findById(1L).orElseGet(() -> repository.save(
                new OrderEntity(1L, "demo-customer", new BigDecimal("42.50"), "CONFIRMED")));
    }
}
