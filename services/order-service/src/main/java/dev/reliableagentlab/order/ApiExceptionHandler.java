package dev.reliableagentlab.order;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(OrderNotFoundException.class)
    ResponseEntity<Map<String, Object>> handleNotFound(OrderNotFoundException exception) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
                "error", Map.of("code", "ORDER_NOT_FOUND", "message", exception.getMessage())));
    }

    @ExceptionHandler(DemoMysqlUnavailableException.class)
    ResponseEntity<Map<String, Object>> handleMysqlUnavailable(DemoMysqlUnavailableException exception) {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                "error", Map.of("code", "DEMO_MYSQL_UNAVAILABLE", "message", exception.getMessage())));
    }

    @ExceptionHandler(DownstreamFailureException.class)
    ResponseEntity<Map<String, Object>> handleDownstreamFailure(DownstreamFailureException exception) {
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(Map.of(
                "error", Map.of("code", exception.code(), "message", "downstream preview failed")));
    }
}
