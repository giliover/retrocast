from retro_live.logging_setup import setup

if __name__ == '__main__':
    setup()
    from retro_live.ui import RetroUI
    RetroUI().run()
