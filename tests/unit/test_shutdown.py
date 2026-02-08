"""Tests for graceful shutdown signal handling."""

import asyncio
import signal

import pytest

from libs.core.shutdown import setup_signal_handlers


@pytest.mark.asyncio
async def test_setup_signal_handlers_sets_event():
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    assert not shutdown_event.is_set()

    # Trigger the signal handler that was registered
    signal.raise_signal(signal.SIGINT)

    # Give the event loop a chance to process
    await asyncio.sleep(0.01)
    assert shutdown_event.is_set()


@pytest.mark.asyncio
async def test_shutdown_event_not_set_initially():
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)
    assert not shutdown_event.is_set()


@pytest.mark.asyncio
async def test_multiple_signals_are_idempotent():
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    signal.raise_signal(signal.SIGINT)
    await asyncio.sleep(0.01)
    assert shutdown_event.is_set()

    # Setting again should be fine (idempotent)
    signal.raise_signal(signal.SIGINT)
    await asyncio.sleep(0.01)
    assert shutdown_event.is_set()
