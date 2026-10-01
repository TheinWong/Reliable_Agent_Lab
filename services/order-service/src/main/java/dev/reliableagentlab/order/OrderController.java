package dev.reliableagentlab.order;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final OrderQueryService service;
    private final CheckoutPreviewService preview;

    public OrderController(OrderQueryService service, CheckoutPreviewService preview) {
        this.service = service;
        this.preview = preview;
    }

    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> getOrder(@PathVariable long id) {
        return ResponseEntity.ok(service.findById(id));
    }

    @GetMapping("/{id}/checkout-preview")
    public ResponseEntity<CheckoutPreviewResponse> checkoutPreview(@PathVariable long id) {
        return ResponseEntity.ok(preview.preview(id));
    }
}
