package dev.reliableagentlab.order;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:order-context;MODE=MySQL;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "app.inventory-url=http://localhost:18081",
        "app.payment-url=http://localhost:18082"
})
class OrderServiceContextTest {
    @Test
    void contextLoadsWithCheckoutPreviewDependencies() {
    }
}
