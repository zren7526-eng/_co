from symboltable import SymbolTable
from vmwriter import SEGMENT

BINOPS = set('+-*/&|<>=')
OP_CMD = {'+': 'add', '-': 'sub', '&': 'and', '|': 'or',
          '<': 'lt', '>': 'gt', '=': 'eq'}


class CompilationEngine:
    def __init__(self, tokenizer, vmwriter):
        self.tk = tokenizer
        self.vm = vmwriter
        self.st = SymbolTable()
        self.class_name = ''
        self.if_count = 0
        self.while_count = 0

    # ---------- 小工具 ----------
    def _next(self):
        self.tk.advance()
        return self.tk.tokenType(), self.tk.value()

    def _peek_is(self, *vals):
        t, v = self.tk.peek()
        return t in ('KEYWORD', 'SYMBOL') and v in vals

    def _expect(self, val):
        t, v = self._next()
        if t not in ('KEYWORD', 'SYMBOL') or v != val:
            raise SyntaxError(f"預期 {val!r}，但得到 {v!r}")

    def _push_var(self, name):
        kind = self.st.kindOf(name)
        if kind is None:
            raise NameError(f"未定義的變數：{name}")
        self.vm.writePush(SEGMENT[kind], self.st.indexOf(name))

    def _pop_var(self, name):
        kind = self.st.kindOf(name)
        if kind is None:
            raise NameError(f"未定義的變數：{name}")
        self.vm.writePop(SEGMENT[kind], self.st.indexOf(name))

    # ---------- 程式結構 ----------
    def compileClass(self):
        self._expect('class')
        _, self.class_name = self._next()
        self._expect('{')
        while self._peek_is('static', 'field'):
            self.compileClassVarDec()
        while self._peek_is('constructor', 'function', 'method'):
            self.compileSubroutine()
        self._expect('}')

    def compileClassVarDec(self):
        _, kind = self._next()          # static / field
        _, type_ = self._next()
        _, name = self._next()
        self.st.define(name, type_, kind)
        while self._peek_is(','):
            self._next()
            _, name = self._next()
            self.st.define(name, type_, kind)
        self._expect(';')

    def compileSubroutine(self):
        _, sub_kind = self._next()      # constructor / function / method
        self._next()                    # 回傳型別
        _, name = self._next()
        self.st.startSubroutine()
        self.if_count = 0
        self.while_count = 0
        if sub_kind == 'method':
            self.st.define('this', self.class_name, 'arg')   # argument 0
        self._expect('(')
        self.compileParameterList()
        self._expect(')')
        self._expect('{')
        n_locals = 0
        while self._peek_is('var'):
            n_locals += self.compileVarDec()
        self.vm.writeFunction(f'{self.class_name}.{name}', n_locals)
        if sub_kind == 'constructor':
            self.vm.writePush('constant', self.st.varCount('field'))
            self.vm.writeCall('Memory.alloc', 1)
            self.vm.writePop('pointer', 0)
        elif sub_kind == 'method':
            self.vm.writePush('argument', 0)
            self.vm.writePop('pointer', 0)
        self.compileStatements()
        self._expect('}')

    def compileParameterList(self):
        if self._peek_is(')'):
            return
        while True:
            _, type_ = self._next()
            _, name = self._next()
            self.st.define(name, type_, 'arg')
            if self._peek_is(','):
                self._next()
            else:
                break

    def compileVarDec(self):
        self._expect('var')
        _, type_ = self._next()
        count = 0
        while True:
            _, name = self._next()
            self.st.define(name, type_, 'var')
            count += 1
            if self._peek_is(','):
                self._next()
            else:
                break
        self._expect(';')
        return count

    # ---------- 語句 ----------
    def compileStatements(self):
        while True:
            if self._peek_is('let'):
                self.compileLet()
            elif self._peek_is('if'):
                self.compileIf()
            elif self._peek_is('while'):
                self.compileWhile()
            elif self._peek_is('do'):
                self.compileDo()
            elif self._peek_is('return'):
                self.compileReturn()
            else:
                break

    def compileDo(self):
        self._expect('do')
        self._compileSubroutineCall()
        self.vm.writePop('temp', 0)     # 丟掉回傳值
        self._expect(';')

    def compileLet(self):
        self._expect('let')
        _, name = self._next()
        is_array = False
        if self._peek_is('['):
            is_array = True
            self._next()
            self._push_var(name)
            self.compileExpression()
            self._expect(']')
            self.vm.writeArithmetic('add')      # 陣列位址 = base + index
        self._expect('=')
        self.compileExpression()
        self._expect(';')
        if is_array:
            self.vm.writePop('temp', 0)
            self.vm.writePop('pointer', 1)
            self.vm.writePush('temp', 0)
            self.vm.writePop('that', 0)
        else:
            self._pop_var(name)

    def compileWhile(self):
        n = self.while_count
        self.while_count += 1
        self.vm.writeLabel(f'WHILE_EXP{n}')
        self._expect('while')
        self._expect('(')
        self.compileExpression()
        self._expect(')')
        self.vm.writeArithmetic('not')
        self.vm.writeIf(f'WHILE_END{n}')
        self._expect('{')
        self.compileStatements()
        self._expect('}')
        self.vm.writeGoto(f'WHILE_EXP{n}')
        self.vm.writeLabel(f'WHILE_END{n}')

    def compileIf(self):
        n = self.if_count
        self.if_count += 1
        self._expect('if')
        self._expect('(')
        self.compileExpression()
        self._expect(')')
        self.vm.writeArithmetic('not')
        self.vm.writeIf(f'IF_FALSE{n}')
        self._expect('{')
        self.compileStatements()
        self._expect('}')
        if self._peek_is('else'):
            self._next()
            self.vm.writeGoto(f'IF_END{n}')
            self.vm.writeLabel(f'IF_FALSE{n}')
            self._expect('{')
            self.compileStatements()
            self._expect('}')
            self.vm.writeLabel(f'IF_END{n}')
        else:
            self.vm.writeLabel(f'IF_FALSE{n}')

    def compileReturn(self):
        self._expect('return')
        if self._peek_is(';'):
            self.vm.writePush('constant', 0)    # void 也要回傳 0
        else:
            self.compileExpression()
        self._expect(';')
        self.vm.writeReturn()

    # ---------- 運算式 ----------
    def compileExpression(self):
        self.compileTerm()
        while True:
            t, v = self.tk.peek()
            if t == 'SYMBOL' and v in BINOPS:
                self._next()
                self.compileTerm()
                if v == '*':
                    self.vm.writeCall('Math.multiply', 2)
                elif v == '/':
                    self.vm.writeCall('Math.divide', 2)
                else:
                    self.vm.writeArithmetic(OP_CMD[v])
            else:
                break

    def compileTerm(self):
        t, v = self._next()
        if t == 'INT_CONST':
            self.vm.writePush('constant', v)
        elif t == 'STRING_CONST':
            self.vm.writePush('constant', len(v))
            self.vm.writeCall('String.new', 1)
            for ch in v:
                self.vm.writePush('constant', ord(ch))
                self.vm.writeCall('String.appendChar', 2)
        elif t == 'KEYWORD':
            if v == 'true':
                self.vm.writePush('constant', 0)
                self.vm.writeArithmetic('not')
            elif v in ('false', 'null'):
                self.vm.writePush('constant', 0)
            elif v == 'this':
                self.vm.writePush('pointer', 0)
            else:
                raise SyntaxError(f"運算式裡不該出現關鍵字 {v!r}")
        elif t == 'SYMBOL':
            if v == '(':
                self.compileExpression()
                self._expect(')')
            elif v == '-':
                self.compileTerm()
                self.vm.writeArithmetic('neg')
            elif v == '~':
                self.compileTerm()
                self.vm.writeArithmetic('not')
            else:
                raise SyntaxError(f"運算式裡不該出現符號 {v!r}")
        elif t == 'IDENTIFIER':
            nt, nv = self.tk.peek()
            if nt == 'SYMBOL' and nv == '[':             # 陣列
                self._push_var(v)
                self._next()
                self.compileExpression()
                self._expect(']')
                self.vm.writeArithmetic('add')
                self.vm.writePop('pointer', 1)
                self.vm.writePush('that', 0)
            elif nt == 'SYMBOL' and nv in ('(', '.'):    # 呼叫
                self._compileSubroutineCall(first=v)
            else:                                        # 一般變數
                self._push_var(v)

    def _compileSubroutineCall(self, first=None):
        if first is None:
            _, first = self._next()
        n_args = 0
        if self._peek_is('.'):
            self._next()
            _, sub = self._next()
            if self.st.kindOf(first):        # obj.method(...)
                self._push_var(first)
                full = f'{self.st.typeOf(first)}.{sub}'
                n_args = 1
            else:                            # Class.function(...)
                full = f'{first}.{sub}'
        else:                                # method(...) → this.method(...)
            self.vm.writePush('pointer', 0)
            full = f'{self.class_name}.{first}'
            n_args = 1
        self._expect('(')
        n_args += self.compileExpressionList()
        self._expect(')')
        self.vm.writeCall(full, n_args)

    def compileExpressionList(self):
        if self._peek_is(')'):
            return 0
        n = 1
        self.compileExpression()
        while self._peek_is(','):
            self._next()
            self.compileExpression()
            n += 1
        return n