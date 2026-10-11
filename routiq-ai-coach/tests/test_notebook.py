from pathlib import Path

import pytest

nbformat = pytest.importorskip("nbformat", reason="Install the notebook extra to verify notebooks")
NOTEBOOK = Path(__file__).parents[1] / "chat_llm.ipynb"


@pytest.mark.parametrize("cell_index", [3, 4, 5])
def test_later_cell_runs_with_fresh_namespace(monkeypatch, cell_index):
    monkeypatch.setattr("builtins.input", lambda prompt: "exit")
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    namespace = {"__name__": "__notebook_test__"}
    exec(compile(notebook.cells[cell_index].source, "standalone-cell", "exec"), namespace)
    assert namespace["project_root"] == NOTEBOOK.parent.resolve()
    if cell_index >= 4:
        assert "client" in namespace


def test_notebook_structure_and_clean_outputs():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    assert len(notebook.cells) == 6
    assert notebook.cells[0].cell_type == "markdown"
    for cell in notebook.cells[1:]:
        assert cell.cell_type == "code"
        assert cell.execution_count is None
        assert cell.outputs == []
        assert "responses.create(" not in cell.source


@pytest.mark.parametrize("messages", [
    ["", "/help", "/samples", "/status", "How was my week?", "/reset", "Hello", "quit"],
    ["x" * 4001, "exit"],
])
def test_notebook_cells_run_offline(monkeypatch, capsys, messages):
    answers = iter(messages)
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    namespace = {"__name__": "__notebook_test__"}
    for i, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            exec(compile(cell.source, f"chat_llm.ipynb:cell-{i}", "exec"), namespace)
    output = capsys.readouterr().out
    assert "OFFLINE_FOUNDATION" in output
    assert "Session ended" in output
    if len(messages) > 2:
        assert "not implemented yet" in output
        assert len(namespace["local_history"]) == 1
    else:
        assert "invalid" in output
        assert namespace["local_history"] == []


@pytest.mark.parametrize("choice", ["", "ENABLE LIVE"])
def test_live_requires_consent_and_missing_credentials_stays_offline(monkeypatch, capsys, choice):
    from app.config.settings import LiveSettings
    def missing_settings(*args):
        raise ValueError("Missing credentials")
    monkeypatch.setattr(LiveSettings, "load", missing_settings)
    answers = iter(["/live", choice, "/status", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    namespace = {"__name__": "__notebook_test__"}
    exec(compile(notebook.cells[5].source, "live-choice-cell", "exec"), namespace)
    assert namespace["notebook_app"].state.coach_service is None
    assert "may incur API charges" in capsys.readouterr().out


@pytest.mark.parametrize("confirmation", ["ENABLE LIVE", "enable live", "  Enable   Live  ", "yes", "YES"])
def test_notebook_live_roundtrip_with_mock_provider(monkeypatch, capsys, confirmation):
    from app.config.settings import LiveSettings
    from app.services.chat_service import LiveCoachService
    from pydantic import SecretStr
    import app.services.chat_service as services
    configured = LiveSettings(api_key=SecretStr("TEST_ONLY"), model="test-model", project_root=NOTEBOOK.parent)
    monkeypatch.setattr(LiveSettings, "load", lambda *args: configured)
    monkeypatch.setattr(services, "LiveCoachService", lambda s: LiveCoachService(s, lambda *args: "You could try a small habit after an existing routine."))
    answers = iter(["/live", confirmation, "Help me start a reading habit", "/offline", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    namespace = {"__name__": "__notebook_test__"}
    exec(compile(notebook.cells[5].source, "mock-live-notebook", "exec"), namespace)
    assert "small habit" in capsys.readouterr().out
    assert namespace["notebook_app"].state.coach_service is None
