import yaml
import sys

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
            elif (nodetype == 'return_statement'):
                return ReturnStatement(D)
            elif (nodetype == 'expression'):
                return ExpressionNode(D)
            elif (nodetype == 'term'):
                return TermNode(D)
            elif (nodetype == 'base_expression'):
                return BaseExpressionNode(D)
            elif (nodetype == 'function_call'):
                return FunctionCallNode(D)
            elif (nodetype == 'method_call'):
                return MethodCallNode(D)
            elif (nodetype == 'function_call_parameter'):
                return FunctionCallParameterNode(D)
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
    
    def count(self, x):
        if (type(x) != str) or (type(self.data) == str):
            raise TypeError
        c = 0
        for y in self.data:
            if x in y:
                c += 1
        return c
    
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
        func_name = 'sn_' + self['identifier'].data
        statements = '    '.join([x.to_code() for x in self['statements']])
        return f'{func_type} {func_name}() {{\n    {statements}}}'

class StatementNode(Node):
    def to_code(self):
        return self[0].to_code()

class VarStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data
        expr_code = self['expression'].to_code()
        return f'auto {var_name} = {expr_code};\n'

class ConstStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data
        expr_code = self['expression'].to_code()
        return f'const auto {var_name} = {expr_code};\n'

class SetStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data
        assign_op = self['assignment_op']
        expr_code = self['expression'].to_code()
        return f'{var_name} {assign_op} {expr_code};\n'

class PrintStatement(Node):
    def to_code(self):
        expr_code = [x.to_code() for x in self]
        expr_code.append('std::endl;\n')
        return 'std::cout << ' + ' << '.join(expr_code)

class RunStatement(Node):
    def to_code(self):
        if 'function_call' in self:
            return self['function_call'].to_code() + ';\n'
        elif 'method_call' in self:
            obj = 'sn_' + self['identifier'].data
            return obj + self['method_call'].to_code() + ';\n'

class ReturnStatement(Node):
    def to_code(self):
        expr_code = self['expression'].to_code()
        return f'return {expr_code}\n'

class ExpressionNode(Node):
    def to_code(self):
        code = ''
        for i in range(len(self.data)):
            cur = self[i]
            if (cur.nodetype == 'unary_op') or (cur.nodetype == 'infix_op'):
                code += ' ' + cur.data + ' '
            elif cur.nodetype == 'term':
                code += cur.to_code()
            else:
                raise TypeError
        return code

class TermNode(Node):
    def to_code(self):
        code = ''
        for x in self:
            if x.nodetype == 'base_expression':
                code = x.to_code()
            elif x.nodetype == 'field_access':
                code += '.sn_' + x['identifier'].data
            elif x.nodetype == 'method_call':
                raise NotImplementedError
            elif x.nodetype == 'index_call':
                raise NotImplementedError
        return code

class BaseExpressionNode(Node):
    def to_code(self):
        if 'function_call' in self:
            return 'sn_function()'
        elif 'constructor_call' in self:
            raise NotImplementedError
        elif 'identifier' in self:
            return 'sn_' + self['identifier'].data
        elif 'literal' in self:
            return self['literal'][0].data
        elif 'expression' in self:
            return '(' + self['expression'].to_code() + ')'

class FunctionCallNode(Node):
    def to_code(self):
        code = 'sn_' + self['identifier'].data + '('
        params = []
        for x in self['function_call_parameters']:
            params.append(x.to_code())
        code += ', '.join(params) + ')'
        return code

class MethodCallNode(Node):
    def to_code(self):
        code = '.sn_' + self['identifier'].data + '('
        params = []
        for x in self['function_call_parameters']:
            params.append(x.to_code())
        code += ', '.join(params) + ')'
        return code

class FunctionCallParameterNode(Node):
    def to_code(self):
        return self['expression'].to_code()


def main():
    lines = []
    for line in sys.stdin:
        lines.append(line)
    my_yaml = ''.join(lines)
    
    try:
        tree = yaml.safe_load(my_yaml)[0]
    except yaml.YAMLError as e:
        print(e)
        exit()

    functions = Node.create(tree)
    function_code = []
    for x in functions:
        function_code.append(x.to_code())
    code = '#include <iostream>\n\n'
    code += '\n\n'.join(function_code)
    print(code)


if __name__ == '__main__':    
    main()