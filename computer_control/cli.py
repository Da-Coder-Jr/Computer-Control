import argparse, asyncio, importlib, os
from .core import manager

def main():
    p=argparse.ArgumentParser(prog="computer-control")
    p.add_argument("goal",nargs="*",help="Objective")
    p.add_argument("--verbose",action="store_true")
    p.add_argument("--voice",action="store_true")
    p.add_argument("--model",help="override model id")
    p.add_argument("--plugin",action="append",help="plugin in plugins/")
    args=p.parse_args()

    if args.model: os.environ["POLL_MODEL"]=args.model
    goal=" ".join(args.goal) or input("Objective> ")
    plugmods=[importlib.import_module(f"computer_control.plugins.{n}") for n in (args.plugin or [])]
    asyncio.run(manager.run(goal, verbose=args.verbose, plugins=plugmods))
