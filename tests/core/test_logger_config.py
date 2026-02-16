import logging

from src.core.logger_config import LoggerConfig


def test_setup_is_idempotent():
    LoggerConfig._configured = False

    LoggerConfig.setup(level=logging.WARNING)
    first_handlers = list(logging.getLogger().handlers)
    first_level = logging.getLogger().level

    LoggerConfig.setup(level=logging.INFO)

    assert LoggerConfig._configured is True
    assert logging.getLogger().handlers == first_handlers
    assert logging.getLogger().level == first_level


def test_get_logger_calls_setup_when_needed(monkeypatch):
    LoggerConfig._configured = False
    called = {"setup": False}

    def fake_setup(level: int = logging.INFO):
        called["setup"] = True
        LoggerConfig._configured = True

    monkeypatch.setattr(LoggerConfig, "setup", fake_setup)

    logger = LoggerConfig.get_logger("test")

    assert called["setup"] is True
    assert logger.name == "test"
