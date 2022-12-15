

import os
from os.path import dirname

parent_dir = dirname(__file__) + '/..'

vars = {}
vars['DIR'] = os.path.realpath(parent_dir)
vars['USER'] = os.getlogin()

for file_name in os.listdir(parent_dir):
    if file_name.endswith('.template'):
        with open(f'{parent_dir}/{file_name}', 'r') as fd:
            text = fd.read()
        for key, value in vars.items():
            text = text.replace(f'---{key}---', value)
        with open(f'{parent_dir}/{file_name[:-9]}', 'w') as fd:
            fd.write(text)
