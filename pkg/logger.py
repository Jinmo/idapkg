"""
Logging module
"""
import logging, sys

def getLogger(name):
    """
    Returns a logger. Wrapper of logging.getLogger
    """
    logger = logging.getLogger(name)
    return logger


def _install_handler():
    logger = logging.getLogger('pkg')
    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(message)s", None)
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.setLevel(logging.INFO)
    return


_install_handler()
