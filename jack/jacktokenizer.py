import re
import sys

KEYWORDS = {
    'class', 'constructor', 'function', 'method', 'field', 'static', 'var',
    'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this',
    'let', 'do', 'if', 'else', 'while', 'return',
}

# 順序很重要：comment 要排在 symbol 前面，否則 "/" 會被當成除號
TOKEN_RE = re.compile(r'''
    (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<string>"[^"\n]*")
  | (?P<int>\d+)
  | (?P<word>[A-Za-z_]\w*)
  | (?P<symbol>[{}()\[\].,;+\-*/&|<>=~])
  | (?P<ws>\s+)
''', re.VERBOSE | re.DOTALL)


class JackTokenizer:
    def __init__(self, text):
        self.tokens = self._tokenize(text)   # [(type, value), ...]
        self.pos = -1

    def _tokenize(self, text):
        tokens = []
        i = 0
        while i < len(text):
            m = TOKEN_RE.match(text, i)
            if not m:
                raise SyntaxError(f"無法辨識的字元 {text[i]!r}（位置 {i}）")
            kind = m.lastgroup
            s = m.group()
            if kind == 'string':
                tokens.append(('STRING_CONST', s[1:-1]))
            elif kind == 'int':
                tokens.append(('INT_CONST', int(s)))
            elif kind == 'word':
                tokens.append(('KEYWORD' if s in KEYWORDS else 'IDENTIFIER', s))
            elif kind == 'symbol':
                tokens.append(('SYMBOL', s))
            # comment 和 ws 直接略過
            i = m.end()
        return tokens

    def hasMoreTokens(self):
        return self.pos + 1 < len(self.tokens)

    def advance(self):
        self.pos += 1

    def peek(self):
        """看下一個 token 但不前進（CompilationEngine 之後會用到）"""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return (None, None)

    def tokenType(self):
        return self.tokens[self.pos][0]

    def value(self):
        return self.tokens[self.pos][1]

    # 以下對應 nand2tetris 規格的方法名稱
    def keyWord(self):
        return self.value()

    def symbol(self):
        return self.value()

    def identifier(self):
        return self.value()

    def intVal(self):
        return self.value()

    def stringVal(self):
        return self.value()


if __name__ == '__main__':
    # 測試：python jack/jacktokenizer.py 11/Seven/Main.jack
    with open(sys.argv[1], encoding='utf-8') as f:
        tk = JackTokenizer(f.read())
    while tk.hasMoreTokens():
        tk.advance()
        print(tk.tokenType(), tk.value())