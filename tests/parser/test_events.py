"""Tests for Event and EventBuffer."""

from __future__ import annotations

from xsdmesh.parser.events import Event, EventBuffer, EventType


class TestEventType:
    """Test EventType enum."""

    def test_event_types_exist(self) -> None:
        """Test all event types exist."""
        assert EventType.START_ELEMENT.value == "start"
        assert EventType.END_ELEMENT.value == "end"
        assert EventType.TEXT.value == "text"
        assert EventType.COMMENT.value == "comment"


class TestEvent:
    """Test Event NamedTuple."""

    def test_event_creation(self) -> None:
        """Test Event creation."""
        event = Event(
            type=EventType.START_ELEMENT,
            element=None,
            text=None,
            line=10,
            column=5,
        )
        assert event.type == EventType.START_ELEMENT
        assert event.element is None
        assert event.text is None
        assert event.line == 10
        assert event.column == 5

    def test_event_with_text(self) -> None:
        """Test Event with text."""
        event = Event(
            type=EventType.TEXT,
            element=None,
            text="Hello",
            line=10,
            column=5,
        )
        assert event.text == "Hello"


class TestEventBuffer:
    """Test EventBuffer."""

    def test_initialization(self) -> None:
        """Test EventBuffer initialization."""
        buffer = EventBuffer()
        assert buffer.current is None

    def test_initialization_with_custom_maxlen(self) -> None:
        """Test EventBuffer with custom maxlen."""
        buffer = EventBuffer(maxlen=5)
        # No direct way to test maxlen, but we can verify it doesn't crash
        assert buffer is not None

    def test_push_event(self) -> None:
        """Test pushing event to buffer."""
        buffer = EventBuffer()
        event = Event(EventType.START_ELEMENT, None, None, 1, 0)

        buffer.push(event)
        assert buffer.lookahead(1) == event

    def test_consume_event(self) -> None:
        """Test consuming event from buffer."""
        buffer = EventBuffer()
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.END_ELEMENT, None, None, 2, 0)

        buffer.push(event1)
        buffer.push(event2)

        consumed = buffer.consume()
        assert consumed == event1
        assert buffer.current == event1

    def test_consume_empty_buffer(self) -> None:
        """Test consuming from empty buffer returns None."""
        buffer = EventBuffer()
        assert buffer.consume() is None
        assert buffer.current is None

    def test_lookahead_single(self) -> None:
        """Test lookahead(1)."""
        buffer = EventBuffer()
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.END_ELEMENT, None, None, 2, 0)

        buffer.push(event1)
        buffer.push(event2)

        assert buffer.lookahead(1) == event1
        assert buffer.lookahead(1) == event1  # Should not consume

    def test_lookahead_multiple(self) -> None:
        """Test lookahead with n>1."""
        buffer = EventBuffer()
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.TEXT, None, "text", 2, 0)
        event3 = Event(EventType.END_ELEMENT, None, None, 3, 0)

        buffer.push(event1)
        buffer.push(event2)
        buffer.push(event3)

        assert buffer.lookahead(1) == event1
        assert buffer.lookahead(2) == event2
        assert buffer.lookahead(3) == event3

    def test_lookahead_out_of_range(self) -> None:
        """Test lookahead beyond buffer size returns None."""
        buffer = EventBuffer()
        event = Event(EventType.START_ELEMENT, None, None, 1, 0)

        buffer.push(event)

        assert buffer.lookahead(1) == event
        assert buffer.lookahead(2) is None

    def test_lookahead_invalid_n(self) -> None:
        """Test lookahead with invalid n returns None."""
        buffer = EventBuffer()
        event = Event(EventType.START_ELEMENT, None, None, 1, 0)

        buffer.push(event)

        assert buffer.lookahead(0) is None
        assert buffer.lookahead(-1) is None

    def test_can_lookahead(self) -> None:
        """Test can_lookahead method."""
        buffer = EventBuffer()
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.END_ELEMENT, None, None, 2, 0)

        buffer.push(event1)
        buffer.push(event2)

        assert buffer.can_lookahead(1)
        assert buffer.can_lookahead(2)
        assert not buffer.can_lookahead(3)

    def test_buffer_ring_behavior(self) -> None:
        """Test buffer ring behavior with maxlen=3."""
        buffer = EventBuffer(maxlen=3)
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.TEXT, None, "a", 2, 0)
        event3 = Event(EventType.TEXT, None, "b", 3, 0)
        event4 = Event(EventType.END_ELEMENT, None, None, 4, 0)

        buffer.push(event1)
        buffer.push(event2)
        buffer.push(event3)
        buffer.push(event4)  # Should evict event1

        # event1 should be evicted, event2 should be first
        assert buffer.lookahead(1) == event2
        assert buffer.lookahead(2) == event3
        assert buffer.lookahead(3) == event4

    def test_consume_advances_buffer(self) -> None:
        """Test consume() advances buffer position."""
        buffer = EventBuffer()
        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.END_ELEMENT, None, None, 2, 0)

        buffer.push(event1)
        buffer.push(event2)

        buffer.consume()  # Consume event1
        assert buffer.lookahead(1) == event2

    def test_current_property(self) -> None:
        """Test current property after consume."""
        buffer = EventBuffer()
        event = Event(EventType.START_ELEMENT, None, None, 1, 0)

        buffer.push(event)
        assert buffer.current is None  # Not consumed yet

        buffer.consume()
        assert buffer.current == event  # Now current is set

    def test_clear_buffer(self) -> None:
        """Test clear() method."""
        buffer = EventBuffer()
        event = Event(EventType.START_ELEMENT, None, None, 1, 0)

        buffer.push(event)
        buffer.clear()

        assert buffer.current is None
        assert buffer.lookahead(1) is None

    def test_len_method(self) -> None:
        """Test __len__() method."""
        buffer = EventBuffer()
        assert len(buffer) == 0

        event1 = Event(EventType.START_ELEMENT, None, None, 1, 0)
        event2 = Event(EventType.END_ELEMENT, None, None, 2, 0)

        buffer.push(event1)
        assert len(buffer) == 1

        buffer.push(event2)
        assert len(buffer) == 2
