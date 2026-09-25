package io.github.theinwong.reliableagentlab.demo.order.api;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.theinwong.reliableagentlab.demo.order.application.OrderNotFoundException;
import io.github.theinwong.reliableagentlab.demo.order.application.OrderService;
import io.github.theinwong.reliableagentlab.demo.order.domain.Order;
import io.github.theinwong.reliableagentlab.demo.order.domain.OrderStatus;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderService orderService;

    @Test
    void createsOrder() throws Exception {
        when(orderService.create(2001L, 2)).thenReturn(existingOrder());

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId":2001,"quantity":2}
                                """))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "http://localhost/api/orders/1001"))
                .andExpect(jsonPath("$.id").value(1001))
                .andExpect(jsonPath("$.productId").value(2001))
                .andExpect(jsonPath("$.quantity").value(2))
                .andExpect(jsonPath("$.status").value("CREATED"));
    }

    @Test
    void getsOrder() throws Exception {
        when(orderService.findById(1001L)).thenReturn(existingOrder());

        mockMvc.perform(get("/api/orders/1001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1001))
                .andExpect(jsonPath("$.status").value("CREATED"));
    }

    @Test
    void rejectsInvalidCreateRequest() throws Exception {
        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId":0,"quantity":0}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid request"));
    }

    @Test
    void returnsNotFoundForMissingOrder() throws Exception {
        when(orderService.findById(1001L)).thenThrow(new OrderNotFoundException(1001L));

        mockMvc.perform(get("/api/orders/1001"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Order not found"))
                .andExpect(jsonPath("$.detail").value("Order not found: 1001"));
    }

    @Test
    void rejectsNonPositiveOrderId() throws Exception {
        mockMvc.perform(get("/api/orders/0"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid request"));
    }

    @Test
    void returnsServiceUnavailableWhenDatabaseFails() throws Exception {
        when(orderService.findById(anyLong()))
                .thenThrow(new DataAccessResourceFailureException("MySQL unavailable"));

        mockMvc.perform(get("/api/orders/1001"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.title").value("Database unavailable"))
                .andExpect(jsonPath("$.detail")
                        .value("The order store is temporarily unavailable"));
    }

    private static Order existingOrder() {
        return new Order(1001L, 2001L, 2, OrderStatus.CREATED);
    }
}
