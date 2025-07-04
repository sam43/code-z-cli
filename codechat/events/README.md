# Event Flow Diagram

```
[CLI/Input] --(USER_INPUT)--> [EventBus] --(handlers)--> [Domain/UseCases, Data, Output]
[Session Load/Save] --(SESSION_LOAD/SAVE)--> [EventBus] --(handlers)--> [Data, Domain]
[File Read] --(FILE_READ)--> [EventBus] --(handlers)--> [Data, Output]
```

- All communication between layers is via events.
- Handlers are registered for each event type.
