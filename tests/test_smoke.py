import subprocess, sys, json, pathlib, importlib
def test_import():
    import computer_control
def test_cli_help():
    out=subprocess.check_output([sys.executable,"-m","computer_control","--help"])
    assert b"Objective" in out
