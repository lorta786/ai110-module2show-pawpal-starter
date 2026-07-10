"""Ensures the project root is importable so tests can `import pawpal_system`.

Its mere presence at the repo root puts this directory on ``sys.path``, so both
``pytest`` and ``python -m pytest`` resolve the ``pawpal_system`` module.
"""
