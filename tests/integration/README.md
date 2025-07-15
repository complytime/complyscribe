# Integration Testing

The purpose of the integration tests is to validate that complyscribe produces output that downstream utilities, like complyctl, can consume.

The `complyctl_home` fixture in `tests/integration/conftest.py` will download, cache, and install complyctl to a temporary directory per test.

If integration tests fail, your cached complyctl download may be stale; delete `/tmp/complyscribe-complyctl-cache` and try again.

