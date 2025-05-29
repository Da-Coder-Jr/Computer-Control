def load(name): import importlib; return importlib.import_module(f".{name}",__package__)
