def load(name:str):
    import importlib, pkg_resources
    return importlib.import_module(f".{name}", __package__)
