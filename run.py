# -*- coding: utf-8 -*-
import argparse
import logging
import sys
import multiprocessing as mp

from ppc_helper.ppc_helper import PPCHelper


def create_logger(logpath=None):
    fmt, dfmt = '%(asctime)s|%(levelname)s|%(message)s', '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config')
    parser.add_argument('--log', help='Path to log')
    return parser.parse_args()


def main():
    args = parse_args()
    create_logger(args.log)
    config_file = args.config
    if config_file is None:
        config_file = 'ppc_helper/config_prod.json'

    ppc = PPCHelper(config_file)
    logging.info('Bot launched')
    ppc.read_config()
    ppc.apply_config()
    ppc.set_handlers_variables()
    logging.info('Config accepted')
    try:
        ppc.create_db_pool()
        ppc.create_bot()
        p1 = mp.Process(target=ppc.run_task_manager)
        p1.start()
        ppc.run_bot()
    finally:
        ppc.stop_bot()
        ppc.stop_task_manager()


if __name__ == '__main__':
    try:
        main()
    except:
        sys.exit()





    



