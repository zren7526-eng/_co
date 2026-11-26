class SymbolTable:
    def __init__(self):
        self.class_table = {}   # static, field
        self.sub_table = {}     # arg, var
        self.counts = {'static': 0, 'field': 0, 'arg': 0, 'var': 0}

    def startSubroutine(self):
        """進入新的 function/method/constructor 時呼叫，清空子程式範圍"""
        self.sub_table = {}
        self.counts['arg'] = 0
        self.counts['var'] = 0

    def define(self, name, type_, kind):
        """kind: 'static' | 'field' | 'arg' | 'var'"""
        index = self.counts[kind]
        self.counts[kind] += 1
        entry = (type_, kind, index)
        if kind in ('static', 'field'):
            self.class_table[name] = entry
        else:
            self.sub_table[name] = entry

    def varCount(self, kind):
        return self.counts[kind]

    def _lookup(self, name):
        # 子程式範圍優先，找不到再找類別範圍
        if name in self.sub_table:
            return self.sub_table[name]
        return self.class_table.get(name)

    def kindOf(self, name):
        e = self._lookup(name)
        return e[1] if e else None

    def typeOf(self, name):
        e = self._lookup(name)
        return e[0] if e else None

    def indexOf(self, name):
        e = self._lookup(name)
        return e[2] if e else None