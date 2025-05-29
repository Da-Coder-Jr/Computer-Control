def test_import():
    import computer_control

def test_cli_help():
    import subprocess, sys
    subprocess.check_output([sys.executable,"-m","computer_control","--help"])
