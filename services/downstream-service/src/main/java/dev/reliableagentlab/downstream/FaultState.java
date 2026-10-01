package dev.reliableagentlab.downstream;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.time.Instant;

import org.springframework.stereotype.Component;

@Component
public class FaultState {
    private final AtomicBoolean active = new AtomicBoolean(false);
    private final AtomicReference<Instant> activatedAt = new AtomicReference<>();

    public boolean isActive() {
        return active.get();
    }

    public boolean setActive(boolean value) {
        boolean changed = active.getAndSet(value) != value;
        if (changed) {
            activatedAt.set(value ? Instant.now() : null);
        }
        return changed;
    }

    public String activatedAt() {
        Instant value = activatedAt.get();
        return value == null ? "" : value.toString();
    }
}
