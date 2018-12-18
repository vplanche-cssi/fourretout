# coding: utf-8
import logging

import os

import errno

import pywps.configuration as config
import sys

cfg_file = os.environ.get('PYWPS_CFG', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pywps.cfg"))

LOGGER = logging.getLogger('Helper')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
LOGGER.addHandler(ch)


def safe_create_dirs(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def create_cfg_dirs():
    config.load_configuration(cfg_file)
    _dir = os.path.abspath(config.get_config_value("server", "workdir"))
    LOGGER.info("Creating working directory: {}".format(_dir))
    safe_create_dirs(_dir)
    _dir = os.path.abspath(config.get_config_value("server", "outputpath"))
    LOGGER.info("Creating output directory: {}".format(_dir))
    safe_create_dirs(_dir)
    _dir = os.path.abspath(os.path.dirname(config.get_config_value("logging", "file")))
    LOGGER.info("Creating log directory: {}".format(_dir))
    safe_create_dirs(_dir)


create_cfg_dirs()


def getlogger(name):
    logger = logging.getLogger(name)

    config.load_configuration(cfg_file)

    if config.get_config_value('logging', 'file') and config.get_config_value('logging', 'level_'+ name):
        logger.setLevel(getattr(logging, config.get_config_value('logging', 'level_' + name)))
        fh = logging.FileHandler(config.get_config_value('logging', 'file'))
        fh.setFormatter(logging.Formatter(config.get_config_value('logging', 'format')))
        logger.addHandler(fh)
    else:  # NullHandler | StreamHandler
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

    return logger
