package dev.reliableagentlab.order;

import java.util.concurrent.atomic.AtomicBoolean;

import org.springframework.stereotype.Component;

@Component
public class FaultState {
    private final AtomicBoolean redisUnavailable = new AtomicBoolean(false);
    private final AtomicBoolean mysqlUnavailable = new AtomicBoolean(false);

    public boolean isRedisUnavailable() {
        return redisUnavailable.get();
    }

    public boolean setRedisUnavailable(boolean unavailable) {
        return redisUnavailable.getAndSet(unavailable) != unavailable;
    }

    public boolean isMysqlUnavailable() {
        return mysqlUnavailable.get();
    }

    public boolean setMysqlUnavailable(boolean unavailable) {
        return mysqlUnavailable.getAndSet(unavailable) != unavailable;
    }
}
