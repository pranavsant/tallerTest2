"""
Feed entity.

A Feed is a data ingestion source (webhook, polling endpoint, stream, or
manual entry) whose events are processed by the Overseer AI to generate
incidents and alerts.

The entity protects its own invariants:
- name must be 1–200 characters
- source_type must be one of the recognised :class:`FeedSourceType` values
- endpoint_url, when present, must be a syntactically valid http(s) URL, and
  is required for source types that are driven by an endpoint
- polling_interval_seconds, when set, must fall within the permitted bounds

Enable/disable is modelled as a status transition that never destroys the feed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from src.domain.exceptions import (
    InvalidFeedNameError,
    InvalidFeedUrlError,
    InvalidPollingIntervalError,
)
from src.domain.value_objects.feed_source_type import FeedSourceType
from src.domain.value_objects.feed_status import FeedStatus


class Feed:
    """Core Feed entity."""

    MAX_NAME_LENGTH = 200

    # Polling cadence bounds: no tighter than every 5 seconds (to protect the
    # upstream source) and no looser than once a day.
    MIN_POLLING_INTERVAL_SECONDS = 5
    MAX_POLLING_INTERVAL_SECONDS = 86_400

    # Fallback cadence for polling feeds that don't set an explicit interval.
    DEFAULT_POLLING_INTERVAL_SECONDS = 300

    # Exponential-backoff bounds applied after consecutive ingestion failures.
    # The delay doubles each failure (interval * 2**failures) but is never
    # allowed to exceed this ceiling so a feed is always eventually retried.
    MAX_BACKOFF_SECONDS = 3_600

    _ALLOWED_URL_SCHEMES = ("http", "https")

    def __init__(
        self,
        *,
        feed_id: str | None = None,
        name: str,
        source_type: FeedSourceType,
        endpoint_url: str | None = None,
        polling_interval_seconds: int | None = None,
        config: dict[str, Any] | None = None,
        status: FeedStatus = FeedStatus.ACTIVE,
        is_enabled: bool = True,
        last_ingested_at: datetime | None = None,
        consecutive_failures: int = 0,
        last_error: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._id = feed_id or str(uuid.uuid4())
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)
        self._status = status
        self._is_enabled = is_enabled
        self._last_ingested_at = last_ingested_at
        self._consecutive_failures = max(0, consecutive_failures)
        self._last_error = last_error
        self._config = dict(config) if config else {}

        # source_type is set first so URL validation can consult it.
        self._source_type = source_type

        # Delegate validation to setters so it is reused on mutation.
        self.name = name
        self.endpoint_url = endpoint_url
        self.polling_interval_seconds = polling_interval_seconds

    # ── Identity ───────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def last_ingested_at(self) -> datetime | None:
        return self._last_ingested_at

    @property
    def consecutive_failures(self) -> int:
        """Number of consecutive failed polls since the last success."""
        return self._consecutive_failures

    @property
    def last_error(self) -> str | None:
        """Reason the most recent poll failed, if it failed."""
        return self._last_error

    # ── Mutable attributes with validation ─────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        stripped = value.strip()
        if not stripped or len(stripped) > self.MAX_NAME_LENGTH:
            raise InvalidFeedNameError(
                f"Feed name must be 1–{self.MAX_NAME_LENGTH} characters, got '{value}'"
            )
        self._name = stripped
        self._touch()

    @property
    def source_type(self) -> FeedSourceType:
        return self._source_type

    @source_type.setter
    def source_type(self, value: FeedSourceType) -> None:
        self._source_type = value
        # Re-validate the URL against the new source type's requirements.
        self.endpoint_url = self._endpoint_url
        self._touch()

    @property
    def endpoint_url(self) -> str | None:
        return self._endpoint_url

    @endpoint_url.setter
    def endpoint_url(self, value: str | None) -> None:
        normalised = value.strip() if value else None

        if normalised:
            parsed = urlparse(normalised)
            if parsed.scheme not in self._ALLOWED_URL_SCHEMES or not parsed.netloc:
                raise InvalidFeedUrlError(
                    f"endpoint_url must be a valid http(s) URL, got '{value}'"
                )
        elif self._source_type.requires_endpoint():
            raise InvalidFeedUrlError(
                f"A '{self._source_type.value}' feed requires an endpoint_url"
            )

        self._endpoint_url = normalised
        self._touch()

    @property
    def polling_interval_seconds(self) -> int | None:
        return self._polling_interval_seconds

    @polling_interval_seconds.setter
    def polling_interval_seconds(self, value: int | None) -> None:
        if value is not None:
            if (
                value < self.MIN_POLLING_INTERVAL_SECONDS
                or value > self.MAX_POLLING_INTERVAL_SECONDS
            ):
                raise InvalidPollingIntervalError(
                    "polling_interval_seconds must be between "
                    f"{self.MIN_POLLING_INTERVAL_SECONDS} and "
                    f"{self.MAX_POLLING_INTERVAL_SECONDS}, got {value}"
                )
        self._polling_interval_seconds = value
        self._touch()

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    @config.setter
    def config(self, value: dict[str, Any] | None) -> None:
        self._config = dict(value) if value else {}
        self._touch()

    # ── Status / enablement ─────────────────────────────────────────────────

    @property
    def status(self) -> FeedStatus:
        return self._status

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    def enable(self) -> None:
        """Enable the feed, resuming ingestion without recreating it."""
        self._is_enabled = True
        # Move out of the disabled state back to active, unless the feed is in
        # an error state that should persist until explicitly cleared.
        if self._status == FeedStatus.DISABLED:
            self._status = FeedStatus.ACTIVE
        self._touch()

    def disable(self) -> None:
        """Disable the feed, pausing ingestion while preserving the record."""
        self._is_enabled = False
        self._status = FeedStatus.DISABLED
        self._touch()

    def is_due_for_polling(self) -> bool:
        """Whether this feed should currently be polled.

        Only enabled, polling-type feeds that are not paused or disabled are
        eligible. The scheduler still owns the cadence; this guards against
        polling a feed an operator has explicitly stood down.
        """
        return (
            self._is_enabled
            and self._source_type.is_polling()
            and self._status not in (FeedStatus.PAUSED, FeedStatus.DISABLED)
        )

    # ── Ingestion outcomes & backoff ─────────────────────────────────────────

    def effective_interval_seconds(self) -> int:
        """The configured polling cadence, or the platform default."""
        return self._polling_interval_seconds or self.DEFAULT_POLLING_INTERVAL_SECONDS

    def next_poll_delay_seconds(self) -> int:
        """Seconds to wait before the next poll, honouring exponential backoff.

        With no recent failures this is simply the effective interval. After
        *n* consecutive failures the delay is ``interval * 2**n``, capped at
        :attr:`MAX_BACKOFF_SECONDS` so a persistently failing feed is still
        retried roughly hourly rather than abandoned.
        """
        interval = self.effective_interval_seconds()
        if self._consecutive_failures == 0:
            return interval
        # Cap the exponent so 2**n cannot overflow into an absurd delay.
        exponent = min(self._consecutive_failures, 20)
        backed_off = interval * (2**exponent)
        return min(backed_off, self.MAX_BACKOFF_SECONDS)  # type: ignore[no-any-return]

    def record_ingestion_success(self, *, at: datetime | None = None) -> None:
        """Record a successful poll: clears backoff and stamps the time."""
        self._last_ingested_at = at or datetime.now(timezone.utc)
        self._consecutive_failures = 0
        self._last_error = None
        # A previously-erroring feed that polls cleanly returns to active.
        if self._status == FeedStatus.ERROR:
            self._status = FeedStatus.ACTIVE
        self._touch()

    def record_ingestion_failure(self, error: str) -> None:
        """Record a failed poll: increments backoff and flags the error state."""
        self._consecutive_failures += 1
        self._last_error = error
        self._status = FeedStatus.ERROR
        self._touch()

    # ── Internals ───────────────────────────────────────────────────────────

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"Feed(id={self._id!r}, name={self._name!r}, "
            f"source_type={self._source_type}, status={self._status}, "
            f"is_enabled={self._is_enabled})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Feed):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
