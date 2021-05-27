import scope

indent_level = 0

# Should be constructed with 'create', not regular constructor
class Node:
    def create(D):
        if type(D) == dict:
            assert(len(D) == 1)
            nodetype = list(D.keys())[0]
            if (nodetype == 'function'):
                return FunctionNode(D)
            elif (nodetype == 'function_parameter'):
                return FunctionParameterNode(D)
            elif (nodetype == 'type'):
                return TypeNode(D)
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
            elif (nodetype == 'break_statement'):
                return BreakStatement(D)
            elif (nodetype == 'continue_statement'):
                return ContinueStatement(D)
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
            elif (nodetype == 'for_loop'):
                return ForLoopNode(D)
            elif (nodetype == 'while_loop'):
                return WhileLoopNode(D)
            elif (nodetype == 'if_block'):
                return IfBlock(D)
            elif (nodetype == 'match_block'):
                return MatchBlock(D)
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
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = scope.ScopeObject(scope.currentscope)

        if 'type' in self:
            func_type = self['type'].to_code()
        else:
            func_type = 'void'
        func_name = 'sn_' + self['identifier'].data
        func_parameters = ', '.join([x.to_code() for x in self['function_parameters']])
        statements = newindent.join([x.to_code() for x in self['statements']])
        if (statements != ''):
            code = f'{func_type} {func_name}({func_parameters}) {{\n{newindent}{statements}{oldindent}}}'
        else:
            code = f'{func_type} {func_name}({func_parameters}) {{\n\n{oldindent}}}'

        indent_level -= 1
        scope.currentscope = scope.currentscope.parent

        return code

class FunctionParameterNode(Node):
    def to_code(self):
        code = self['type'].to_code()
        if 'accessor' in self:
            accessor = self['accessor'].data
            if accessor == 'mutate':
                code += '&'
        else:
            accessor = 'look'
        var_name = 'sn_' + self['identifier'].data
        code += ' ' + var_name

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.currentscope.add_binding(scope.ParameterObject(var_name, accessor))

        return code

class TypeNode(Node):
    def to_code(self):
        base = self['base_type'].data
        if base == 'Int':
            code = 'int64_t'
        elif base == 'Bool':
            code = 'bool'
        elif base == 'String':
            code = 'std::string'
        elif base == 'Float':
            code = 'double'
        elif base == 'Char':
            code = 'char'
        elif base == 'Vector':
            code = 'SN_Vector'
        elif base == 'Array':
            code = 'SN_Array'
        else:
            raise NotImplementedError
        if 'type' in self:  # Generic type
            return code + '<' + self['type'].to_code() + '>'
        else:
            return code

class StatementNode(Node):
    def to_code(self):
        scope.line_number = self[0].data
        return self[1].to_code()

class VarStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=True))

        expr_code = self['expression'].to_code()
        return f'auto {var_name} = {expr_code};\n'

class ConstStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=False))

        expr_code = self['expression'].to_code()
        return f'const auto {var_name} = {expr_code};\n'

class SetStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        if scope.currentscope.check_set(var_name):
            assign_op = self['assignment_op']
            expr_code = self['expression'].to_code()
            return f'{var_name} {assign_op} {expr_code};\n'
        else:
            raise scope.SereneScopeError(scope.line_number, self['identifier'].data)

class PrintStatement(Node):
    def to_code(self):
        expr_code = [x.to_code() for x in self]
        expr_code.append('std::endl;\n')
        return 'std::cout << ' + ' << '.join(expr_code)

class RunStatement(Node):
    def to_code(self):
        return self['term'].to_code() + ';\n'

class ReturnStatement(Node):
    def to_code(self):
        expr_code = self['expression'].to_code()
        return f'return {expr_code};\n'

class BreakStatement(Node):
    def to_code(self):
        return 'break;\n'

class ContinueStatement(Node):
    def to_code(self):
        return 'continue;\n'

class ExpressionNode(Node):
    def to_code(self, enclosing_accessor=None):     # enclosing_accessor should only be passed to top-level expression with an applied accessor
        code = ''
        last_term = None
        for i in range(len(self.data)):
            cur = self[i]
            if (cur.nodetype == 'unary_op') or (cur.nodetype == 'infix_op'):
                if type(cur.data) != str:
                    code += ' ' + cur[0].data + ' '
                else:
                    code += ' ' + cur.data + ' '
            elif cur.nodetype == 'term':
                last_term = cur
                code += cur.to_code()
            else:
                raise TypeError
        
        self.is_temporary = (self.count('term') > 1) or (last_term.is_temporary)
        if not self.is_temporary:
            self.var_to_access = last_term.var_to_access
            if enclosing_accessor is not None:
                if not scope.currentscope.check_pass(self.var_to_access, enclosing_accessor):
                    raise scope.SereneScopeError(scope.line_number, self.var_to_access[3:])

        return code

class TermNode(Node):
    def to_code(self):
        base_expr = self[0]
        inner_expr = base_expr[0]

        if inner_expr.nodetype == 'identifier':
            self.is_temporary = False
            self.var_to_access = 'sn_' + self[0][0].data
            code = self.var_to_access
        elif (inner_expr.nodetype == 'expression'):
            code = '(' + inner_expr.to_code() + ')'
            self.is_temporary = inner_expr.is_temporary
            if not self.is_temporary:
                self.var_to_access = inner_expr.var_to_access
        else:
            code = base_expr.to_code()
            self.is_temporary = True

        for i in range(1, len(self.data)):
            x = self[i]
            if x.nodetype == 'field_access':
                code += '.sn_' + x['identifier'].data
            elif x.nodetype == 'method_call':
                if not self.is_temporary:
                    if 'mutate_method_symbol' in x:
                        if not scope.currentscope.check_pass(self.var_to_access, 'mutate'):
                            raise scope.SereneScopeError(scope.line_number, self.var_to_access[3:])
                    # Method calls return temporary values, so only the first method call in a term needs to be scope-checked
                    self.is_temporary = True
                code += x.to_code()
            elif x.nodetype == 'index_call':
                code += '[' + x['expression'].to_code() + ']'
        return code

class BaseExpressionNode(Node):
    def to_code(self):
        if 'function_call' in self:
            return self['function_call'].to_code()
        elif 'constructor_call' in self:
            raise NotImplementedError
        elif 'identifier' in self:
            var_name = 'sn_' + self['identifier'].data
            if scope.currentscope.check_read(var_name):     # If the variable also needs to be mutated/moved, that will already be checked within TermNode or ExpressionNode
                return var_name
            else:
                raise scope.SereneScopeError(scope.line_number, self['identifier'].data)
        elif 'literal' in self:
            if 'bool_literal' in self['literal']:
                return self['literal'][0].data.lower()
            else:
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
        if 'accessor' in self:
            accessor = self['accessor'].data
        else:
            accessor = 'look'
        
        code = self['expression'].to_code(enclosing_accessor=accessor) # This will raise exceptions for incorrect accesses
        return code

class ForLoopNode(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = scope.ScopeObject(scope.currentscope)

        loopvar = 'sn_' + self['identifier'].data
        scope.currentscope.add_binding(scope.VariableObject(loopvar, mutable=False))

        statements = newindent.join([x.to_code() for x in self['statements']])
        if self.count('expression') == 2:   # start and endpoint
            startval = self[1].to_code()
            endval = self[2].to_code()
            code = f'for (int {loopvar} = {startval}; {loopvar} < {endval}; {loopvar}++) {{\n{newindent}{statements}{oldindent}}}\n'
        else:
            myrange = self['expression'].to_code()
            code = f'for (const auto& {loopvar} : {myrange}) {{\n{newindent}{statements}{oldindent}}}\n'
        
        indent_level -= 1
        scope.currentscope = scope.currentscope.parent

        return code

class WhileLoopNode(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = scope.ScopeObject(scope.currentscope)

        statements = newindent.join([x.to_code() for x in self['statements']])
        condition = self['expression'].to_code()
        code = f'while ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        indent_level -= 1
        scope.currentscope = scope.currentscope.parent

        return code

class IfBlock(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = scope.ScopeObject(scope.currentscope)

        code = ''
        cur = self['if_branch']
        statements = newindent.join([x.to_code() for x in cur['statements']])
        condition = cur['expression'].to_code()
        code += f'if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        scope.currentscope = scope.currentscope.parent

        if 'elseif_branch' in self:
            scope.currentscope = scope.ScopeObject(scope.currentscope)

            cur = self['elseif_branch']
            statements = newindent.join([x.to_code() for x in cur['statements']])
            condition = cur['expression'].to_code()
            code += f'{oldindent}else if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        if 'else_branch' in self:
            scope.currentscope = scope.ScopeObject(scope.currentscope)

            cur = self['else_branch']
            statements = newindent.join([x.to_code() for x in cur['statements']])
            code += f'{oldindent}else {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        indent_level -= 1
        return code

class MatchBlock(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        subject = self['expression'].to_code()
        branches = []
        for x in self:
            if x.nodetype == 'match_branch':
                scope.currentscope = scope.ScopeObject(scope.currentscope)
                
                if 'expression' in x:
                    conditions = []
                    for i in range(len(x.data) - 1):    # skip last element, which is 'statements'; all others are expressions
                        conditions.append('(' + x[i].to_code() + ' == ' + subject + ')')
                    conditions = ' or '.join(conditions)
                    if 'statements' in x:
                        statements = newindent.join([y.to_code() for y in x['statements']])
                    else:
                        statements = x['statement'].to_code()
                    branchcode = f'if ({conditions}) {{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                else:   # 'else' branch in 'match' block
                    if 'statements' in x:
                        statements = newindent.join([y.to_code() for y in x['statements']])
                    else:
                        statements = x['statement'].to_code()
                    branchcode = f'{{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                
                scope.currentscope = scope.currentscope.parent
        indent_level -= 1
        return (f'{oldindent}else ').join(branches)
