package io.github.theinwong.reliableagentlab.demo.order.api;

import io.github.theinwong.reliableagentlab.demo.order.application.OrderNotFoundException;
import jakarta.validation.ConstraintViolationException;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail handleOrderNotFound(OrderNotFoundException exception) {
        return problem(HttpStatus.NOT_FOUND, "Order not found", exception.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, ConstraintViolationException.class})
    ProblemDetail handleInvalidRequest(Exception exception) {
        return problem(
                HttpStatus.BAD_REQUEST,
                "Invalid request",
                "One or more request values are invalid");
    }

    @ExceptionHandler(DataAccessException.class)
    ProblemDetail handleDatabaseUnavailable(DataAccessException exception) {
        return problem(
                HttpStatus.SERVICE_UNAVAILABLE,
                "Database unavailable",
                "The order store is temporarily unavailable");
    }

    private static ProblemDetail problem(HttpStatus status, String title, String detail) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, detail);
        problem.setTitle(title);
        return problem;
    }
}
