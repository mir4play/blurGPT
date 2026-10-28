import core.runtime as runtime_module


def test_ensure_runtime_directories_creates_model_directory(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    monkeypatch.setattr(runtime_module, "MODEL_DIR", model_dir)

    assert not model_dir.exists()

    runtime_module.ensure_runtime_directories()

    assert model_dir.is_dir()
    assert list(model_dir.iterdir()) == []
