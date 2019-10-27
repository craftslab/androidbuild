#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import sys

LEVEL = logging.INFO


class Build:
    DEFINED = 'Defined'
    MODULE = 'Module'


build = [
    Build.MODULE,
    Build.DEFINED
]


def write(name, data):
    """
    JSON FORMAT:
    {
      "adbd": ["system/core/adb"],
      "ext": ["frameworks/base"]
    }
    """
    with open(name, 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def update(cache, data):
    buf = cache.copy()
    buf.update(data)

    return buf


def fetch(name):
    global build
    data = {}

    def _fetch(_data, _direct):
        """
        REFER: '# Module: adbd'
        REFER: '# Module:'
               '# adbd'
        REFER: '# Defined: system/core/adb/Android.bp:494:1'
        REFER: '# Defined:
               '# system/core/adb/Android.bp:494:1'
        """
        if _direct is True:
            if _data.startswith('# '):
                return _data.replace('# ', '').strip(), True
        _buf = None
        _status = False
        for item in build:
            if _data.startswith('# %s:' % item):
                _buf = _data.split(':')[1].strip()
                _status = True
                break
        return _buf, _status

    with open(name, 'r') as f:
        buf = {}
        _index = 0
        _next = False
        for line in f:
            if len(line.strip().strip('\n').strip('\r')) == 0 or not line.startswith('#'):
                continue
            if _index < len(build):
                found, status = _fetch(line, _next)
                if status is True:
                    if found is not None and len(found) != 0:
                        buf[build[_index]] = found
                        _next = False
                        _index += 1
                    else:
                        _next = True
            if _index == len(build):
                if buf.get(Build.MODULE, None) is not None and buf.get(Build.DEFINED, None) is not None:
                    data[buf[Build.MODULE]] = [os.path.dirname(buf[Build.DEFINED].split(':')[0])]
                buf[Build.MODULE] = None
                buf[Build.DEFINED] = None
                _index = 0

    return data


def load(name):
    with open(name, 'r') as f:
        data = json.load(f)

    return data


def _logging(level, name):
    if level == logging.DEBUG:
        fmt = '%(filename)s: %(levelname)s: %(message)s'
    else:
        fmt = '%(levelname)s: %(message)s'

    if name is None:
        logging.basicConfig(format=fmt, level=level)
    else:
        if not os.path.exists(name):
            logging.basicConfig(filename=name, format=fmt, level=level)
        else:
            print('%s already exist' % name)
            return False

    return True


def main():
    global LEVEL
    desc = 'Soong Cache'

    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i', '--input-ninja', dest='input_ninja',
                        required=True,
                        help='input ninja, format: .ninja')
    parser.add_argument('-o', '--output-cache', dest='output_cache',
                        required=True,
                        help='output cache, format: .cache')

    options = parser.parse_args()

    ret = _logging(LEVEL, None)
    if ret is False:
        return -1

    if not os.path.exists(options.input_ninja):
        logging.error('%s not found' % options.input_ninja)
        return -2

    if os.path.exists(options.output_cache):
        cache = load(options.output_cache)
    else:
        cache = {}

    buf = fetch(options.input_ninja)
    if buf is None or len(buf) == 0:
        logging.error('Failed to fetch ninja')
        return -3

    cache = update(cache, buf)
    if cache is None or len(cache) == 0:
        logging.error('Failed to update cache')
        return -4

    write(options.output_cache, cache)

    logging.debug('Done.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
