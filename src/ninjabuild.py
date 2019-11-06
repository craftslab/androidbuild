#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import subprocess
import sys

level = {
    'debug': logging.DEBUG,
    'error': logging.ERROR,
    'info': logging.INFO
}


class Build:
    def __init__(self, cache, name):
        self.cache = cache
        self.name = name

        self.buf = self._load()
        if self.buf is None or len(self.buf) == 0:
            raise Exception('Failed to load cache')

    def _load(self):
        """
        KATI JSON FORMAT:
        {
          "init_first_stage": ["system/core/init"],
          "CarDialerApp": ["packages/apps/Car/Dialer"]
        }

        SOONG JSON FORMAT:
        {
          "adbd": ["system/core/adb"],
          "ext": ["frameworks/base"]
        }
        """
        with open(self.cache, 'r') as f:
            data = json.load(f)

        return data

    def fetch(self):
        target = []
        buf = ''
        _max = ''

        for _target, _paths in self.buf.items():
            for _path in _paths:
                if _path in self.name:
                    if len(_path) > len(_max):
                        _max = _path
                        buf = _target

        if len(buf) != 0:
            target.append(buf)

        for _target, _paths in self.buf.items():
            for _path in _paths:
                if _path == _max:
                    target.append(_target)

        return sorted(list(set(target)))


class Kati(Build):
    def __init__(self, cache, ninja, name):
        Build.__init__(self, cache, name)
        self.ninja = ninja

        self.target = self.fetch()
        if self.target is None or len(self.target) == 0:
            raise Exception('Failed to fetch target')

    def build(self):
        def _build(target):
            cmd = 'ninja -f %s %s' % (self.ninja, target)
            logging.debug(cmd)
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            if proc.returncode != 0 and len(stdout) != 0:
                logging.debug(stdout)
                return stdout
            return None

        out = None
        ret = True

        for item in self.target:
            out = _build(item)
            if out is not None:
                ret = False
                break

        return out, ret


class Soong(Build):
    def __init__(self, cache, ninja, name):
        Build.__init__(self, cache, name)
        self.ninja = ninja

        self.target = self.fetch()
        if self.target is None or len(self.target) == 0:
            raise Exception('Failed to fetch target')

    def build(self):
        def _build(target):
            cmd = 'ninja -f %s %s-soong' % (self.ninja, target)
            logging.debug(cmd)
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            if proc.returncode != 0 and len(stdout) != 0:
                logging.debug(stdout)
                return stdout
            return None

        out = None
        ret = True

        for item in self.target:
            out = _build(item)
            if out is not None:
                ret = False
                break

        return out, ret


def write(data, name):
    with open(name, 'w') as f:
        f.write(data)


def kati(cache, ninja, name):
    try:
        instance = Kati(cache, ninja, name)
        out, status = instance.build()
    except Exception as _:
        return None, False

    return out, status


def soong(cache, ninja, name):
    try:
        instance = Soong(cache, ninja, name)
        out, status = instance.build()
    except Exception as _:
        return None, False

    return out, status


def _logging(_level, name):
    if _level == logging.DEBUG:
        fmt = '%(filename)s: %(levelname)s: %(message)s'
    else:
        fmt = '%(levelname)s: %(message)s'

    if name is None:
        logging.basicConfig(format=fmt, level=_level)
    else:
        if not os.path.exists(name):
            logging.basicConfig(filename=name, format=fmt, level=_level)
        else:
            print('%s already exist' % name)
            return False

    return True


def main():
    global level
    desc = 'Ninja Build'

    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-f', '--file-path', dest='file_path',
                        required=True,
                        help='file path')
    parser.add_argument('-l', '--log-level', dest='log_level',
                        help='log level, type: debug, info, error')
    parser.add_argument('-o', '--output-file', dest='output_file',
                        help='output file, format: .txt')

    kati_group = parser.add_argument_group('kati group')
    kati_group.add_argument('-kc', '--kati-cache', dest='kati_cache',
                            help='kati cache, format: .cache')
    kati_group.add_argument('-kn', '--kati-ninja', dest='kati_ninja',
                            help='kati ninja, format: .ninja')

    soong_group = parser.add_argument_group('soong group')
    soong_group.add_argument('-sc', '--soong-cache', dest='soong_cache',
                             help='soong cache, format: .cache')
    soong_group.add_argument('-sn', '--soong-ninja', dest='soong_ninja',
                             help='soong ninja, format: .ninja')

    options = parser.parse_args()

    if options.log_level is not None and options.log_level in level.keys():
        _level = level[options.log_level]
    else:
        _level = logging.INFO

    ret = _logging(_level, None)
    if ret is False:
        return -1

    if options.output_file is not None and os.path.exists(options.output_file):
        logging.error('%s already exist' % options.output_file)
        return -2

    if options.kati_cache is not None and options.kati_ninja is not None:
        if not os.path.exists(options.kati_cache) or not os.path.exists(options.kati_ninja):
            logging.error('Kati cache or ninja not found')
            return -3
    elif options.kati_cache is None and options.kati_ninja is None:
        pass
    else:
        logging.error('Kati cache or ninja required')
        return -4

    if options.soong_cache is not None and options.soong_ninja is not None:
        if not os.path.exists(options.soong_cache) or not os.path.exists(options.soong_ninja):
            logging.error('Soong cache or ninja not found')
            return -5
    elif options.soong_cache is None and options.soong_ninja is None:
        pass
    else:
        logging.error('Soong cache or ninja required')
        return -6

    if options.soong_cache is not None and options.soong_ninja is not None:
        out, status = soong(options.soong_cache, options.soong_ninja, options.file_path)
        if status is False:
            if out is not None:
                logging.info('Failed to build target')
                if options.output_file is not None:
                    write(out, options.output_file)
                return 0

    if options.kati_cache is not None and options.kati_ninja is not None:
        out, status = kati(options.kati_cache, options.kati_ninja, options.file_path)
        if status is False:
            if out is not None:
                logging.info('Failed to build target')
                if options.output_file is not None:
                    write(out, options.output_file)
                return 0
            else:
                logging.error('Failed to run ninja')
                return -7

    logging.info('Build completed successfully')

    return 0


if __name__ == '__main__':
    sys.exit(main())
