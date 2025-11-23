"""Event types and EventBuffer for SAX parsing with lookahead support.

Provides:
- EventType: Enum for XML events (start, end, text)
- Event: NamedTuple representing a single parse event
- EventBuffer: Ring buffer with lookahead(n) capability using deque(maxlen=3)
"""

from __future__ import annotations

from collections import deque
from enum import Enum
from typing import NamedTuple

from lxml import etree


class EventType(Enum):
    """XML event types for SAX parsing."""

    START_ELEMENT = "start"
    END_ELEMENT = "end"
    TEXT = "text"
    COMMENT = "comment"


class Event(NamedTuple):
    """Single parse event from XML stream.

    Attributes:
        type: Event type (start, end, text, comment)
        element: Element node (None for text/comment)
        text: Text content (None for element events)
        line: Line number in source
        column: Column number in source
    """

    type: EventType
    element: etree._Element | None
    text: str | None
    line: int
    column: int


class EventBuffer:
    """Ring buffer for event lookahead during parsing.

    Uses deque(maxlen=3) for efficient O(1) lookahead.
    Critical for disambiguation:
    - <simpleType> with <restriction> vs <list> vs <union>
    - <complexType> with <simpleContent> vs <complexContent> vs compositor

    Example:
        buffer = EventBuffer()
        buffer.push(event1)
        buffer.push(event2)
        next_event = buffer.lookahead(1)  # Peek ahead without consuming
        current = buffer.consume()  # Get and advance
    """

    def __init__(self, maxlen: int = 3) -> None:
        """Initialize event buffer.

        Args:
            maxlen: Maximum lookahead depth (default 3)
        """
        self._buffer: deque[Event] = deque(maxlen=maxlen)
        self._current: Event | None = None
        self._maxlen = maxlen

    @property
    def current(self) -> Event | None:
        """Current event being processed."""
        return self._current

    def push(self, event: Event) -> None:
        """Add event to buffer.

        Args:
            event: Event to add
        """
        self._buffer.append(event)

    def consume(self) -> Event | None:
        """Get next event and advance position.

        Returns:
            Next event or None if buffer empty
        """
        if not self._buffer:
            self._current = None
            return None

        self._current = self._buffer.popleft()
        return self._current

    def lookahead(self, n: int = 1) -> Event | None:
        """Peek at event n positions ahead without consuming.

        Args:
            n: Number of positions to look ahead (1-based)

        Returns:
            Event at position n or None if not available
        """
        if n < 1 or n > len(self._buffer):
            return None
        return self._buffer[n - 1]

    def can_lookahead(self, n: int) -> bool:
        """Check if lookahead of n positions is possible.

        Args:
            n: Number of positions to check

        Returns:
            True if lookahead is possible
        """
        return 1 <= n <= len(self._buffer)

    def clear(self) -> None:
        """Clear buffer and reset current."""
        self._buffer.clear()
        self._current = None

    def __len__(self) -> int:
        """Number of events in buffer."""
        return len(self._buffer)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"EventBuffer(current={self._current}, buffer={list(self._buffer)})"
