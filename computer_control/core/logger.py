from ..utils.ansi import GREEN, YELLOW, BLUE, RED, RESET
def info(msg):  print(f"{GREEN}{msg}{RESET}")
def warn(msg):  print(f"{YELLOW}{msg}{RESET}")
def error(msg): print(f"{RED}{msg}{RESET}")
def debug(msg): print(f"{BLUE}{msg}{RESET}")
