import sys
import pickle
import traceback
import importlib.util
from pathlib import Path

def load_module_from_file(file_name):
    module_name = file_name.rstrip(".py").replace("/", ".").replace("\\", ".")
    spec = importlib.util.spec_from_file_location(module_name, file_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    else:
        raise ImportError(f"Cannot load module from {file_name}")


def main():
    try:
        with open(sys.argv[1], "rb") as fd:
            loaded_data = pickle.load(fd)
        mod = load_module_from_file(loaded_data['file'])
        callback = mod.__dict__[loaded_data['func']]
        ret = callback(*loaded_data['args'], **loaded_data['kwargs'])
        with open(sys.argv[1], "wb") as fd:
            pickle.dump({ 'ret': ret }, fd)
    except Exception as ex:
        print('Exception in remote call:', traceback.format_exc(), file=sys.stderr)
        try:
            with open(sys.argv[1], "wb") as fd:
                pickle.dump({ 'ex': ex }, fd)
        except:
            try:
                Path(sys.argv[1]).unlink()
            except:
                pass
            raise
    sys.exit(0)

if __name__ == "__main__":
    main()
