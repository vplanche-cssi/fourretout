# coding: utf-8
import logging

import os

import errno

import pywps.configuration as config
import sys

cfg_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pywps.cfg")

LOGGER = logging.getLogger('Helper')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
LOGGER.handlers = []
LOGGER.addHandler(ch)
LOGGER.propagate = False


def run_once(func_to_decorate):

    def wrapper(*args, **kwargs):
        if not wrapper.already_run:
            try:
                return func_to_decorate(*args, **kwargs)
            finally:
                wrapper.already_run = True
    wrapper.already_run = False
    return wrapper


def ensure_conf_loaded(func_to_decorate):
    def wrapper(*args, **kwargs):
        run_once(config.load_configuration)(cfg_file)
        return func_to_decorate(*args, **kwargs)

    return wrapper


@ensure_conf_loaded
def get_config_value(option, section='server'):
    return config.get_config_value(section, option)


@ensure_conf_loaded
def get_config_values(section='server'):
    return config.CONFIG[section]


def safe_create_dirs(dirrectory):
    try:
        os.makedirs(dirrectory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


@ensure_conf_loaded
@run_once
def create_cfg_dirs():
    _dir = os.path.abspath(get_config_value(section='server', option='workdir'))
    LOGGER.info("Creating working directory: {}".format(_dir))
    safe_create_dirs(_dir)
    _dir = os.path.abspath(get_config_value(section='server', option='outputpath'))
    LOGGER.info("Creating output directory: {}".format(_dir))
    safe_create_dirs(_dir)
    _dir = os.path.abspath(os.path.dirname(get_config_value(section='logging', option='file')))
    LOGGER.info("Creating log directory: {}".format(_dir))
    safe_create_dirs(_dir)


@ensure_conf_loaded
def getlogger(name):
    create_cfg_dirs()
    logger = logging.getLogger(name)

    if get_config_value(section='logging', option='file') \
            and get_config_value(section='logging', option='level_co3d'):
        logger.setLevel(getattr(logging, get_config_value(section='logging', option='level_co3d')))
        fh = logging.FileHandler(get_config_value(section='logging', option='file'))
        fh.setFormatter(logging.Formatter(get_config_value(section='logging', option='format')))
        logger.addHandler(fh)
    else:  # NullHandler | StreamHandler
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    return logger
