import yaml

# https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python

# Should be constructed with 'create', not regular constructor
class Node:
    def create(D):
        if type(D) == dict:
            assert(len(D) == 1)
            nodetype = list(D.keys())[0]
            if (nodetype == 'function'):
                return FunctionNode(D)
            elif (nodetype == 'statement'):
                return StatementNode(D)
            elif (nodetype == 'var_statement'):
                return VarStatement(D)
            elif (nodetype == 'const_statement'):
                return ConstStatement(D)
            elif (nodetype == 'set_statement'):
                return SetStatement(D)
            elif (nodetype == 'print_statement'):
                return PrintStatement(D)
            elif (nodetype == 'run_statement'):
                return RunStatement(D)
            elif (nodetype == 'expression'):
                return ExpressionNode(D)
            else:
                return Node(D)
        else:
            raise TypeError

    def __init__(self, D):
        self.nodetype = list(D.keys())[0]
        self.data = D[self.nodetype]
    
    def __getitem__(self, x):
        if type(self.data) == str:
            raise TypeError
        if type(x) == int:
            return Node.create(self.data[x])
        if type(x) == str:
            for y in self.data:
                if x in y:
                    return Node.create(y)
        raise TypeError
    
    def __contains__(self, x):
        if type(self.data) == str:
            raise TypeError
        if type(x) == int:
            return x in self.data[x]
        if type(x) == str:
            for y in self.data:
                if x in y:
                    return True
            return False
        raise TypeError
    
    def __iter__(self):
        self._i = 0
        return self
    
    def __next__(self):
        if self._i == len(self.data):
            raise StopIteration
        
        n = self[self._i]
        self._i += 1
        return n
    
    def __repr__(self):
        if type(self.data) == str:
            return self.data
        else:
            return self.nodetype


class FunctionNode(Node):
    def to_code(self):
        if 'type' not in self:
            func_type = 'void'
        else:
            func_type = self['type']
        func_name = self['identifier']
        statements = '    '.join([x.to_code() for x in self['statements']])
        return f'{func_type} sn_{func_name}() {{\n    {statements}}}'


class StatementNode(Node):
    def to_code(self):
        return self[0].to_code()

class VarStatement(Node):
    def to_code(self):
        var_name = self['identifier']
        expr_code = self['expression'].to_code()
        return f'auto {var_name} = {expr_code};\n'

class ConstStatement(Node):
    def to_code(self):
        var_name = self['identifier']
        expr_code = self['expression'].to_code()
        return f'const {var_name} = {expr_code};\n'

class SetStatement(Node):
    def to_code(self):
        var_name = self['identifier']
        assign_op = self['assignment_op']
        expr_code = self['expression'].to_code()
        return f'{var_name} {assign_op} {expr_code};\n'

class PrintStatement(Node):
    def to_code(self):
        expr_code = [x.to_code() for x in self]
        expr_code.append('endl;\n')
        return 'cout << ' + ' << '.join(expr_code)

class RunStatement(Node):
    def to_code(self):
        return 'sn_function();\n'

class ExpressionNode(Node):
    def to_code(self):
        return 'expr'
        


with open("parsed2.yaml", 'r') as stream:
    try:
        tree = yaml.safe_load(stream)[0]

        functions = Node.create(tree)
        for x in functions:
            print(x.to_code())

    except yaml.YAMLError as exc:
        print(exc)