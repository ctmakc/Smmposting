"""Tests that all workers import and use the graceful shutdown pattern."""

import ast

import pytest

WORKER_MODULES = [
    "apps.worker_ingest.worker",
    "apps.worker_analyze.worker",
    "apps.worker_generate.worker",
    "apps.worker_publish.worker",
    "apps.worker_metrics.worker",
]


@pytest.mark.parametrize("module_path", WORKER_MODULES)
def test_worker_imports_shutdown(module_path):
    """Each worker must import setup_signal_handlers."""
    parts = module_path.replace(".", "/") + ".py"
    with open(parts) as f:
        source = f.read()
    tree = ast.parse(source)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append(alias.name)

    assert "setup_signal_handlers" in imports, (
        f"{module_path} does not import setup_signal_handlers"
    )


@pytest.mark.parametrize("module_path", WORKER_MODULES)
def test_worker_uses_async_with(module_path):
    """Each worker must use 'async with worker' pattern (not 'await worker.run()')."""
    parts = module_path.replace(".", "/") + ".py"
    with open(parts) as f:
        source = f.read()

    assert "async with worker" in source, (
        f"{module_path} does not use 'async with worker' pattern"
    )
    assert "await worker.run()" not in source, (
        f"{module_path} still uses old 'await worker.run()' pattern"
    )


@pytest.mark.parametrize("module_path", WORKER_MODULES)
def test_worker_creates_shutdown_event(module_path):
    """Each worker must create a shutdown event."""
    parts = module_path.replace(".", "/") + ".py"
    with open(parts) as f:
        source = f.read()

    assert "asyncio.Event()" in source, (
        f"{module_path} does not create asyncio.Event()"
    )
    assert "shutdown_event.wait()" in source, (
        f"{module_path} does not await shutdown_event.wait()"
    )
