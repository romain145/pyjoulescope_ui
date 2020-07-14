# Copyright 2020 Jetperch LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from joulescope_ui.paths import paths_current
import json
import logging
import os
import re
from PySide2 import QtCore


log = logging.getLogger(__name__)
MYPATH = os.path.dirname(os.path.abspath(__file__))


def loader(name):
    theme_path = os.path.join(paths_current()['dirs']['themes'], name)
    theme_index = os.path.join(theme_path, 'index.json')
    with open(theme_index, 'r', encoding='utf-8') as f:
        index = json.load(f)
    theme_css = os.path.join(theme_path, 'style.qss')
    if not os.path.isfile(theme_css):
        raise ValueError('generate theme')  # todo
    f = QtCore.QFile(theme_css)
    f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    stream = QtCore.QTextStream(f)
    app = QtCore.QCoreApplication.instance()
    app.setStyleSheet(stream.readAll())
    return index


def preferences_overwrite(index, cmdp):
    profile = cmdp.preferences.profile
    if profile == 'default':
        cmdp.preferences.purge('Appearance/Colors/')
    else:
        for name in cmdp.preferences.match('Appearance/Colors/', profile=profile):
            cmdp.preferences.clear(name, profile)
    for color, value in index['colors'].items():
        name = f'Appearance/Colors/{color}'
        cmdp.preferences.set(name, value, profile)


def theme_source_path(theme_name):
    theme_name = theme_name.split('.')[0]
    path = os.path.join(MYPATH, theme_name)
    return path


def theme_source_index(theme_name):
    path = theme_source_path(theme_name)
    theme_index = os.path.join(path, 'index.json')
    if not os.path.isfile(theme_index):
        raise ValueError('Invalid theme: missing index.json')
    with open(theme_index, 'r', encoding='utf-8') as f:
        index = json.load(f)
    return index


def _theme_source_load_file(theme_name, filename):
    path = theme_source_path(theme_name)
    fname = os.path.join(path, filename)
    if not os.path.isfile(fname):
        raise ValueError(f'Theme could not load source file {filename}')
    with open(fname, 'r', encoding='utf-8') as f:
        return f.read()


def theme_name_parser(theme_name, subtheme_name=None):
    if theme_name is None or not len(theme_name):
        raise ValueError(f'invalid theme name: {theme_name}')
    p = theme_name.split('.')
    if subtheme_name is not None:
        if len(p) != 1:
            log.warning('subtheme specified and in theme_name')
        return p[0], subtheme_name
    if len(p) == 1:  # use default subtheme
        index = theme_source_index(theme_name)
        subtheme_name = next(iter(index['colors']))
        return p[0], subtheme_name
    elif len(p) == 2:
        return p[0], p[1]
    elif len(p) != 2:
        raise ValueError(f'invalid theme name: {theme_name}')


def theme_name_normalize(theme_name, subtheme_name=None):
    parts = theme_name_parser(theme_name, subtheme_name)
    return '.'.join(parts)


def _generate_files(theme_name, theme_files, target_path, colors):
    r = re.compile(r'{%\s*([a-zA-Z0-9_]+)\s*%}')
    target_path = target_path.replace('\\', '/')

    for source in theme_files:
        s = _theme_source_load_file(theme_name, source)
        def replace(matchobj):
            varname = matchobj.group(1)
            if varname == 'path':
                return target_path
            return colors[varname]
        s = r.sub(replace, s)
        with open(os.path.join(target_path, source), 'w', encoding='utf-8') as f:
            f.write(s)


def _generate_images(index):
    src_path = index['generator']['source_path']
    target_path = index['generator']['target_path']
    colors = index['colors']
    for name, image_set in index['images'].items():
        log.info('generate images for %s', name)
        for source in image_set['sources']:
            basename, ext = os.path.splitext(source)
            src = os.path.join(src_path, source)
            with open(src, 'r', encoding='utf-8') as f:
                svg = f.read()
            for filename, subs in image_set['targets']:
                svg_out = svg
                filename = filename.format(basename=basename, ext=ext)
                for substr, replace in subs.items():
                    svg_out = svg_out.replace(substr, colors[replace])
                fname = os.path.join(target_path, filename)
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(svg_out)


def _generate(theme_name, target_path):
    basetheme_name, subtheme_name = theme_name_parser(theme_name)
    if not os.path.isdir(target_path):
        os.makedirs(target_path, exist_ok=True)

    src_path = theme_source_path(theme_name)
    index = theme_source_index(theme_name)
    if index['name'] != basetheme_name:
        raise ValueError(f'theme name mismatch: {index["name"]} != {basetheme_name}')
    index['generator'] = {
        'name': theme_name_normalize(basetheme_name, subtheme_name),
        'source_path': src_path,
        'target_path': target_path,
    }
    index['colors'] = index['colors'][subtheme_name]
    _generate_files(theme_name, index['files'], target_path, index['colors'])
    _generate_images(index)
    with open(os.path.join(target_path, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f)


def theme_loader(theme_name, target_name, generate=None, target_path=None):
    """Load a theme, generating as needed.

    :param theme_name: The theme name given as "{theme}.{subtheme}".
    :param target_name: The target name, usually the profile name.
    :param generate: When True, force generate.
    :param target_path: The target path.  Used to override the default for
        unit testing.
    :return: The theme index.
    """
    if target_path is None:
        target_path = paths_current()['dirs']['themes']
    target_path = os.path.join(target_path, target_name)
    theme_index = os.path.join(target_path, 'index.json')
    if bool(generate) or not os.path.isfile(theme_index):
        _generate(theme_name, target_path)

    with open(theme_index, 'r', encoding='utf-8') as f:
        index = json.load(f)
    files = {}
    for filename in index['files']:
        with open(os.path.join(target_path, filename),'r', encoding='utf-8') as f:
            files[filename] = f.read()
    index['files'] = files
    if 'style.qss' in files:
        app = QtCore.QCoreApplication.instance()
        if app is not None:
            app.setStyleSheet(files['style.qss'])
    return index
