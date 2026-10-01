package dev.reliableagentlab.order;

public class DownstreamFailureException extends RuntimeException {
    private final String code;

    public DownstreamFailureException(String code, Throwable cause) {
        super(code, cause);
        this.code = code;
    }

    public String code() {
        return code;
    }
}
