# 符號表的 kind 對應到 VM 的 segment
SEGMENT = {
    'static': 'static',
    'field': 'this',
    'arg': 'argument',
    'var': 'local',
}


class VMWriter:
    def __init__(self, out_path):
        self.f = open(out_path, 'w', encoding='utf-8', newline='\n')

    def writePush(self, segment, index):
        self.f.write(f'push {segment} {index}\n')

    def writePop(self, segment, index):
        self.f.write(f'pop {segment} {index}\n')

    def writeArithmetic(self, command):
        # add sub neg eq gt lt and or not
        self.f.write(f'{command}\n')

    def writeLabel(self, label):
        self.f.write(f'label {label}\n')

    def writeGoto(self, label):
        self.f.write(f'goto {label}\n')

    def writeIf(self, label):
        self.f.write(f'if-goto {label}\n')

    def writeCall(self, name, n_args):
        self.f.write(f'call {name} {n_args}\n')

    def writeFunction(self, name, n_locals):
        self.f.write(f'function {name} {n_locals}\n')

    def writeReturn(self):
        self.f.write('return\n')

    def close(self):
        self.f.close()