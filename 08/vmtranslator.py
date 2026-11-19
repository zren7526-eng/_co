import sys
from pathlib import Path


# ---------- Parser ----------
def parse(path):
    """讀 .vm，去掉註解與空白，回傳指令清單"""
    commands = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split("//")[0].strip()
            if line:
                commands.append(line.split())
    return commands


# ---------- CodeWriter ----------
class CodeWriter:
    SEG = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}

    def __init__(self):
        self.asm = []
        self.file_name = ""
        self.func_name = ""
        self.label_id = 0
        self.ret_id = 0

    def emit(self, *lines):
        self.asm.extend(lines)

    def set_file(self, name):
        self.file_name = name

    # ----- bootstrap -----
    def write_init(self):
        self.emit("@256", "D=A", "@SP", "M=D")
        self.write_call("Sys.init", 0)

    # ----- 算術 -----
    def write_arithmetic(self, cmd):
        if cmd in ("add", "sub", "and", "or"):
            op = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}[cmd]
            self.emit("@SP", "AM=M-1", "D=M", "A=A-1", f"M={op}")
        elif cmd in ("neg", "not"):
            op = "-M" if cmd == "neg" else "!M"
            self.emit("@SP", "A=M-1", f"M={op}")
        elif cmd in ("eq", "gt", "lt"):
            jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[cmd]
            n = self.label_id
            self.label_id += 1
            self.emit(
                "@SP", "AM=M-1", "D=M", "A=A-1", "D=M-D",
                f"@TRUE_{n}", f"D;{jump}",
                "@SP", "A=M-1", "M=0",
                f"@END_{n}", "0;JMP",
                f"(TRUE_{n})",
                "@SP", "A=M-1", "M=-1",
                f"(END_{n})",
            )
        else:
            raise ValueError(f"未知算術指令：{cmd}")

    # ----- push / pop -----
    def write_push_pop(self, cmd, seg, i):
        if cmd == "push":
            if seg == "constant":
                self.emit(f"@{i}", "D=A")
            elif seg in self.SEG:
                self.emit(f"@{i}", "D=A", f"@{self.SEG[seg]}", "A=D+M", "D=M")
            elif seg == "temp":
                self.emit(f"@{5 + int(i)}", "D=M")
            elif seg == "pointer":
                self.emit(f"@{3 + int(i)}", "D=M")
            elif seg == "static":
                self.emit(f"@{self.file_name}.{i}", "D=M")
            else:
                raise ValueError(f"未知區段：{seg}")
            self.emit("@SP", "A=M", "M=D", "@SP", "M=M+1")
        else:  # pop
            if seg in self.SEG:
                self.emit(
                    f"@{i}", "D=A", f"@{self.SEG[seg]}", "D=D+M",
                    "@R13", "M=D",
                    "@SP", "AM=M-1", "D=M",
                    "@R13", "A=M", "M=D",
                )
            else:
                if seg == "temp":
                    addr = f"@{5 + int(i)}"
                elif seg == "pointer":
                    addr = f"@{3 + int(i)}"
                elif seg == "static":
                    addr = f"@{self.file_name}.{i}"
                else:
                    raise ValueError(f"未知區段：{seg}")
                self.emit("@SP", "AM=M-1", "D=M", addr, "M=D")

    # ----- 流程控制 -----
    def _label(self, name):
        return f"{self.func_name}${name}" if self.func_name else name

    def write_label(self, name):
        self.emit(f"({self._label(name)})")

    def write_goto(self, name):
        self.emit(f"@{self._label(name)}", "0;JMP")

    def write_if(self, name):
        self.emit("@SP", "AM=M-1", "D=M", f"@{self._label(name)}", "D;JNE")

    # ----- 函式 -----
    def write_function(self, name, k):
        self.func_name = name
        self.emit(f"({name})")
        for _ in range(int(k)):
            self.emit("@SP", "A=M", "M=0", "@SP", "M=M+1")

    def write_call(self, name, n):
        ret = f"{name}$ret.{self.ret_id}"
        self.ret_id += 1
        self.emit(f"@{ret}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1")
        for reg in ("LCL", "ARG", "THIS", "THAT"):
            self.emit(f"@{reg}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1")
        self.emit(
            "@SP", "D=M", f"@{int(n) + 5}", "D=D-A", "@ARG", "M=D",
            "@SP", "D=M", "@LCL", "M=D",
            f"@{name}", "0;JMP",
            f"({ret})",
        )

    def write_return(self):
        self.emit(
            "@LCL", "D=M", "@R13", "M=D",          # FRAME = LCL
            "@5", "A=D-A", "D=M", "@R14", "M=D",   # RET = *(FRAME-5)
            "@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D",  # *ARG = pop()
            "@ARG", "D=M+1", "@SP", "M=D",         # SP = ARG+1
        )
        for i, reg in enumerate(("THAT", "THIS", "ARG", "LCL"), start=1):
            self.emit("@R13", "D=M", f"@{i}", "A=D-A", "D=M", f"@{reg}", "M=D")
        self.emit("@R14", "A=M", "0;JMP")


# ---------- 主程式 ----------
def translate_file(writer, path):
    writer.set_file(path.stem)
    for parts in parse(path):
        cmd = parts[0]
        if cmd in ("push", "pop"):
            writer.write_push_pop(cmd, parts[1], parts[2])
        elif cmd == "label":
            writer.write_label(parts[1])
        elif cmd == "goto":
            writer.write_goto(parts[1])
        elif cmd == "if-goto":
            writer.write_if(parts[1])
        elif cmd == "function":
            writer.write_function(parts[1], parts[2])
        elif cmd == "call":
            writer.write_call(parts[1], parts[2])
        elif cmd == "return":
            writer.write_return()
        else:
            writer.write_arithmetic(cmd)


def main():
    if len(sys.argv) < 2:
        print("用法：python vmtranslator.py <檔案.vm 或 資料夾> [--no-init]")
        return

    target = Path(sys.argv[1])
    use_init = "--no-init" not in sys.argv
    writer = CodeWriter()

    if target.is_dir():
        vm_files = sorted(target.glob("*.vm"))
        out_path = target / (target.name + ".asm")
        # 有 Sys.vm 的資料夾才需要 bootstrap
        if use_init and any(f.name == "Sys.vm" for f in vm_files):
            writer.write_init()
    else:
        vm_files = [target]
        out_path = target.with_suffix(".asm")

    for f in vm_files:
        translate_file(writer, f)

    out_path.write_text("\n".join(writer.asm) + "\n", encoding="utf-8")
    print(f"已產生 {out_path}")


if __name__ == "__main__":
    main()