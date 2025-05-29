import argparse, asyncio, importlib
from .core import manager
from .drivers.voice import listen

def main():
    p=argparse.ArgumentParser(prog="computer-control")
    p.add_argument("goal",nargs="*",help="Objective for the computer")
    p.add_argument("--verbose",action="store_true")
    p.add_argument("--voice",action="store_true")
    p.add_argument("--model",help="override model id")
    p.add_argument("--plugin",action="append",help="plugin name in plugins/")
    args=p.parse_args()

    if args.model:
        import os; os.environ["POLL_MODEL"]=args.model

    goal=" ".join(args.goal) or (listen() if args.voice else input("Objective> "))
    plugmods=[importlib.import_module(f"computer_control.plugins.{n}") for n in (args.plugin or [])]
    asyncio.run(manager.run(goal, voice=args.voice, verbose=args.verbose, plugins=plugmods))

if __name__=="__main__":
    main()
