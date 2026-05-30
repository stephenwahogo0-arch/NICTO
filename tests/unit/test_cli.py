"""Test CLI functionality."""
from typer.testing import CliRunner
from nicto.cli.main import app

runner = CliRunner()


def test_version_command():
    """Test version command output."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "NICTO" in result.stdout
    assert "v2.1.0" in result.stdout


def test_doctor_command():
    """Test doctor command runs without error."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    # Should contain some status checks
    assert "Python" in result.stdout or "NICTO" in result.stdout


def test_init_command(tmp_path):
    """Test init command creates .nicto directory."""
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / ".nicto").exists()
        assert (tmp_path / ".nicto" / "config.json").exists()
    finally:
        os.chdir(old_cwd)