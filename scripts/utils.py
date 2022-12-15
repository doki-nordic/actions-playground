

def cmd2bash(path: str):
    path = path.replace('\\', '/')
    if (len(path) > 1) and (path[1] == ':'):
        path = '/' + path[0].lower() + path[2:]
    return path
