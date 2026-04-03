from unittest.mock import MagicMock

import pytest

from yara.cli.commands import CommandContext, dispatch, cmd_exit, cmd_home, cmd_new, cmd_help, cmd_refresh


@pytest.fixture
def ctx():
    return CommandContext(
        conversation=MagicMock(),
        console=MagicMock(),
        signal={},
    )


# --- dispatch() ---

def test_dispatch_non_slash_returns_false(ctx):
    assert dispatch("hello world", ctx) is False


def test_dispatch_known_command_returns_true(ctx):
    assert dispatch("/exit", ctx) is True


def test_dispatch_sets_signal_for_known_command(ctx):
    dispatch("/exit", ctx)
    assert ctx.signal.get("exit") is True


def test_dispatch_unknown_command_returns_true(ctx):
    assert dispatch("/notacommand", ctx) is True


def test_dispatch_unknown_command_prints_error(ctx):
    dispatch("/notacommand", ctx)
    ctx.console.print.assert_called_once()
    printed = ctx.console.print.call_args[0][0]
    assert "notacommand" in printed


def test_dispatch_command_with_trailing_args(ctx):
    # "/exit now" should still dispatch /exit
    assert dispatch("/exit now please", ctx) is True
    assert ctx.signal.get("exit") is True


# --- cmd_exit ---

def test_cmd_exit_sets_exit_signal(ctx):
    cmd_exit(ctx)
    assert ctx.signal["exit"] is True


# --- cmd_home ---

def test_cmd_home_sets_home_signal(ctx):
    cmd_home(ctx)
    assert ctx.signal["home"] is True


# --- cmd_new ---

def test_cmd_new_resets_conversation(ctx, mocker):
    mocker.patch("yara.cli.commands.render_assistant")
    cmd_new(ctx)
    ctx.conversation.reset.assert_called_once()


def test_cmd_new_calls_render_assistant(ctx, mocker):
    mock_render = mocker.patch("yara.cli.commands.render_assistant")
    ctx.conversation.first_assistant_prompt.return_value = "Hello!"
    cmd_new(ctx)
    mock_render.assert_called_once_with("Hello!")


# --- cmd_help ---

def test_cmd_help_prints_to_console(ctx):
    cmd_help(ctx)
    assert ctx.console.print.called


# --- cmd_refresh ---

def test_cmd_refresh_no_project_prints_warning(ctx):
    ctx.project = None
    cmd_refresh(ctx)
    ctx.console.print.assert_called_once()
    printed = ctx.console.print.call_args[0][0]
    assert "No active project" in printed


def test_cmd_refresh_no_project_does_not_ingest(ctx, mocker):
    mock_ingest = mocker.patch("yara.services.ingest.ingest_files_to_db")
    ctx.project = None
    cmd_refresh(ctx)
    mock_ingest.assert_not_called()


def test_cmd_refresh_with_project_calls_ingest(ctx, mocker):
    mock_ingest = mocker.patch("yara.services.ingest.ingest_files_to_db")
    ctx.project = {"id": 1, "ingestion_path": "/tmp/docs"}
    cmd_refresh(ctx)
    mock_ingest.assert_called_once_with("/tmp/docs", 1)
