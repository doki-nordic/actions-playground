
from json import loads
from os import environ
from pathlib import Path
from types import SimpleNamespace

def _dict_to_namespace(d):
    for k in d.keys():
        if isinstance(d[k], dict):
            d[k] = _dict_to_namespace(d[k])
    return SimpleNamespace(**d)

def _load_ctx():
    if 'RUNNER_TEMP' in environ:
        temp_dir = Path(environ['RUNNER_TEMP'])
    else:
        temp_dir = Path(__file__).parent.parent.parent.parent
    d = loads((temp_dir / 'contexts.json').read_bytes())
    return _dict_to_namespace(d)


ctx = _load_ctx()

github = ctx.github
env = ctx.env
vars = ctx.vars
job = ctx.job
steps = ctx.steps
runner = ctx.runner
secrets = ctx.secrets
needs = ctx.needs
inputs = ctx.inputs

