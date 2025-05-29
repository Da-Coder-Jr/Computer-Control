from ..utils.ansi import GREEN,YELLOW,RED,BLUE,RESET
def info(m):  print(f"{GREEN}{m}{RESET}")
def warn(m):  print(f"{YELLOW}{m}{RESET}")
def err(m):   print(f"{RED}{m}{RESET}")
def dbg(m):   print(f"{BLUE}{m}{RESET}")
