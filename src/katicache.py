#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import sys

LEVEL = logging.INFO


class Build:
    BUILD = 'build'
    DESCRIPTION = 'description'


build = [
    Build.DESCRIPTION,
    Build.BUILD
]


def write(name, data):
    """
    JSON FORMAT:
    {
      "init_first_stage": ["system/core/init"],
      "CarDialerApp": ["packages/apps/Car/Dialer"]
    }
    """
    with open(name, 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def update(cache, data):
    buf = cache.copy()
    buf.update(data)

    return buf


def build_java_jar(data, target):
    _target = target[Build.DESCRIPTION].split(':')[-1].strip()
    _target = ''.join([item.replace('_intermediates', '') for item in _target.split('/') if item.endswith('_intermediates')]).strip()
    _output = target[Build.BUILD].split(':')[0].strip()

    if data.get(_target, None) is None:
        data[_target] = {
            'input': [],
            'output': _output
        }
    else:
        pass

    return data


def build_java_src(data, target):
    _target = target[Build.DESCRIPTION].split(':')[-1].strip()
    _input = target[Build.BUILD].split(':')[-1].strip()
    _input = [item.strip() for item in _input.split() if item.strip().endswith('.java')]

    if data.get(_target, None) is None:
        data[_target] = {
            'input': _input,
            'output': None
        }
    else:
        data[_target]['input'].extend(_input)

    return data


def build_c_link(data, target):
    _target = target[Build.DESCRIPTION].split(':')[-1].split()[0].strip()
    _output = target[Build.BUILD].split(':')[0].strip()

    if data.get(_target, None) is None:
        data[_target] = {
            'input': [],
            'output': _output
        }
    else:
        pass

    return data


def build_c_obj(data, target):
    _target, _input = target[Build.DESCRIPTION].split(':')[-1].split('<')

    if data.get(_target.strip(), None) is None:
        data[_target.strip()] = {
            'input': [_input.strip()],
            'output': None
        }
    else:
        data[_target.strip()]['input'].append(_input.strip())

    return data


handler = {
    'AAR': None,
    'Bundle': None,
    'C': build_c_obj,
    'C++': build_c_obj,
    'Dex': None,
    'Executable': build_c_link,
    'Generated': None,
    'Jar': None,
    'Java': build_java_jar,
    'Java source list': build_java_src,
    'Package': None,
    'Prebuilt': None,
    'SharedLib': build_c_link,
    'StaticExecutable': build_c_link,
    'StaticLib': build_c_link,
    'Strip': None,
    'Symbolic': None,
    'Turbine': None,
    'arm C': build_c_obj,
    'arm C++': build_c_obj,
    'build info': None,
    'buildinfo': None,
    'cache fs image': None,
    'debug ram disk': None,
    'dex2oat': None,
    'empty super fs image': None,
    'misc_info.txt': None,
    'odm buildinfo': None,
    'product buildinfo': None,
    'ram disk': None,
    'super fs image for debug': None,
    'super fs image from target files': None,
    'system fs image': None,
    'system_ext buildinfo': None,
    'test harness ram disk': None,
    'thumb C': build_c_obj,
    'thumb C++': build_c_obj,
    'userdata fs image': None,
    'vbmeta image': None,
    'vendor buildinfo': None,
    'vendor fs image': None
}


def rebuild(data):
    """
    INTERMEDIATE JSON
    FORMAT:
    {
      "init_first_stage": {
        "input": ["system/core/init/devices.cpp"],  # C/C++/arm C/arm C++/thumb C/thumb C++
        "output": "out/target/product/generic_arm64/obj/EXECUTABLES/init_first_stage_intermediates/LINKED/init" # Executable/SharedLib/StaticExecutable
      },
      "CarDialerApp": {
        "input": ["packages/apps/Car/Dialer/src/com/android/car/dialer/DialerApplication.java"],  # Java source list
        "output": "out/target/common/obj/APPS/CarDialerApp_intermediates/classes-full-debug.jar"  # Java
      }
    }
    """
    def _rebuild(_data):
        """
        JSON FORMAT:
        {
          "init_first_stage": ["system/core/init"],
          "CarDialerApp": ["packages/apps/Car/Dialer"]
        }
        """
        _buf = {}
        for value in _data.values():
            dirs = [os.path.dirname(item) for item in value['input']]
            if len(dirs) != 0:
                _buf[value['output']] = sorted(list(set(dirs)))
        return _buf

    global handler
    buf = {}

    for item in data:
        target = item[Build.DESCRIPTION].split(':')[0].replace('target', '').replace('Target', '').strip()
        _handler = handler.get(target, None)
        if _handler is not None:
            buf = _handler(buf, item)

    return _rebuild(buf)


def fetch(name):
    global build
    data = []

    def _fetch(_data):
        """
        REFER: 'rule RULENAME'
               ' description = target C: TARGET < INPUT
               ' command = COMMAND
               'build OUTPUT: RULENAME INPUT
        REFER: 'rule RULENAME'
               ' description = target Executable: TARGET (OUTPUT)
               ' command = COMMAND
               'build OUTPUT: RULENAME INPUT
        REFER: 'rule RULENAME'
               ' description = target Java: OUTPUT
               ' command = COMMAND
               'build OUTPUT: RULENAME INPUT
        REFER: 'rule RULENAME'
               ' description = target Java source list: PACKAGE
               ' command = COMMAND
               'build OUTPUT: RULENAME INPUT
        """
        _buf = None
        _build = None
        _status = False
        for item in build:
            if _data.strip().startswith(item):
                _buf = _data.replace(item+' ', '').replace('= ', '').strip()
                _build = item
                _status = True
                break
        return _buf, _build, _status

    with open(name, 'r') as f:
        buf = {}
        _index = 0
        for line in f:
            if len(line.strip().strip('\n').strip('\r')) == 0 or line.startswith('#') or line.startswith('build target:'):
                continue
            if _index < len(build):
                found, _type, status = _fetch(line)
                if status is True and _type == build[_index]:
                    if found is not None and len(found) != 0:
                        buf[build[_index]] = found
                        _index += 1
            if _index == len(build):
                if buf.get(Build.BUILD, None) is not None \
                        and buf.get(Build.DESCRIPTION, None) is not None:
                    data.append(buf.copy())
                buf[Build.BUILD] = None
                buf[Build.DESCRIPTION] = None
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
    desc = 'Kati Cache'

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

    buf = rebuild(buf)
    if buf is None or len(buf) == 0:
        logging.error('Failed to rebuild buffer')
        return -4

    cache = update(cache, buf)
    if cache is None or len(cache) == 0:
        logging.error('Failed to update cache')
        return -5

    write(options.output_cache, cache)

    logging.debug('Done.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
