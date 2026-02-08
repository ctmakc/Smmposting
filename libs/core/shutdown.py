"""Graceful shutdown handling for Temporal workers."""

from __future__ import annotations

import asyncio
import signal

import structlog

logger = structlog.get_logger()


def setup_signal_handlers(shutdown_event: asyncio.Event) -> None:
    """Register SIGINT/SIGTERM handlers that set the shutdown event."""
    loop = asyncio.get_running_loop()

    def _handler(sig: signal.Signals) -> None:
        logger.info("shutdown_signal_received", signal=sig.name)
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handler, sig)
