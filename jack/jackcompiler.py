import os
import sys

from jacktokenizer import JackTokenizer
from vmwriter import VMWriter
from compilationengine import CompilationEngine


def compile_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    out = os.path.splitext(path)[0] + '.vm'
    vm = VMWriter(out)
    try:
        CompilationEngine(JackTokenizer(text), vm).compileClass()
    finally:
        vm.close()
    print(f'{path} -> {out}')


def main():
    if len(sys.argv) != 2:
        print('用法：python jack/jackcompiler.py <資料夾或 .jack 檔>')
        sys.exit(1)
    target = sys.argv[1]
    if os.path.isdir(target):
        files = sorted(os.path.join(target, n)
                       for n in os.listdir(target) if n.endswith('.jack'))
    else:
        files = [target]
    for p in files:
        compile_file(p)


if __name__ == '__main__':
    main()