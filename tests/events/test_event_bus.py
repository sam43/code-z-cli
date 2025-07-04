from codechat.events.event_bus import EventBus

def test_event_bus_pub_sub():
    bus = EventBus()
    result = []
    def handler(data):
        result.append(data)
    bus.subscribe("test_event", handler)
    bus.publish("test_event", 123)
    assert result == [123]
