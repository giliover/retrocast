import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup():
    os.umask(0o077)
    path = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'retrocast'
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    logger = logging.getLogger('retrocast.application')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(path/'application.log',maxBytes=2*1024*1024,backupCount=3,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(threadName)s %(message)s'))
        logger.addHandler(handler)
