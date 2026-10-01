package dev.reliableagentlab.order;

import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Component;

@Component
public class DemoEventRecorder {
    private static final int MAX_EVENTS = 100;
    private final ArrayDeque<DemoEvent> events = new ArrayDeque<>();

    public synchronized void record(String type, String dependency, String detail) {
        if (events.size() == MAX_EVENTS) {
            events.removeFirst();
        }
        events.addLast(new DemoEvent(Instant.now(), type, dependency, detail));
    }

    public synchronized List<DemoEvent> recent() {
        return new ArrayList<>(events);
    }

    public record DemoEvent(Instant observedAt, String type, String dependency, String detail) {
    }
}
