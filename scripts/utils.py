
import re

def cmd2bash(path: str):
    path = path.replace('\\', '/')
    if (len(path) > 1) and (path[1] == ':'):
        path = '/' + path[0].lower() + path[2:]
    return path

def bash_escape(text):
    return re.sub(r'[^ /0-9a-zA-Z_+:;,.=\-]', lambda m: '\\n' if m.group(0) == '\n' else f'\\x{ord(m.group(0)):02x}', text)

def cmd_escape(text):
    return (text
        .replace('%', '%%')
        .replace('^', '^^')
        .replace('&', '^&')
        .replace('<', '^<')
        .replace('>', '^>')
        .replace('|', '^|')
        .replace('\'', '^\'')
        .replace('`', '^`')
        .replace(',', '^,')
        .replace(';', '^;')
        .replace('=', '^=')
        .replace('(', '^(')
        .replace(')', '^)')
        .replace('"', '^"')
        .replace('\r\n', '\n')
        .replace('\n', '^\r\n\r\n')
        )
