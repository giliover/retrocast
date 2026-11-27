"""RetroCast UI package."""
def __getattr__(name):
    if name == 'RetroUI':
        from .app import RetroUI
        return RetroUI
    raise AttributeError(name)
