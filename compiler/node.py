import scope

indent_level = 0

# Base Classes ________________________________________________________________

class NodeMap:
    def __init__(self, L):  # L is a list of Node objects
        if type(L) != list:
            raise TypeError
        self.data = [Node.create(x) for x in L]
    
    def __getitem__(self, x):
        if type(x) == int:
            return self.data[x]
        if type(x) == str:
            for y in self.data:
                if y.nodetype == x:
                    return y
        raise TypeError
    
    def __contains__(self, x):
        if type(x) == int:
            return x in self.data[x]
        if type(x) == str:
            for y in self.data:
                if y.nodetype == x:
                    return True
            return False
        raise TypeError
    
    def count(self, x):
        c = 0
        for y in self.data:
            if y.nodetype == x:
                c += 1
        return c
    
    def __len__(self):
        return len(self.data)

    def __str__(self):
        raise TypeError
    
    def __repr__(self):
        return '\n'.join(repr(x) for x in self.data)

# Node should be constructed with 'create', not regular constructor
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
        inside = D[self.nodetype]
        if type(inside) == list:
            self.data = NodeMap(inside)
        else:
            self.data = inside
        
    def __getitem__(self, x):
        if type(self.data) == NodeMap:
            return self.data[x]
        else:
            raise TypeError
    
    def __contains__(self, x):
        if type(self.data) == NodeMap:
            return x in self.data
        else:
            raise TypeError
    
    def count(self, x):
        if (type(x) != str) or (type(self.data) != NodeMap):
            raise TypeError
        return self.data.count(x)
    
    def __iter__(self):
        if type(self.data) == NodeMap:
            return iter(self.data.data)
        else:
            return iter([])
    
    def __str__(self):
        raise TypeError

    def __repr__(self):
        if type(self.data) == NodeMap:
            return '<' + self.nodetype + '>\n  ' + '\n  '.join(repr(self.data).split('\n')) + '\n</' + self.nodetype + '>'
        else:
            return '<' + self.nodetype + ': ' + repr(self.data if self.data != '' else None) + '>'


# Subclasses __________________________________________________________________

class FunctionNode(Node):
    def __init__(self, D):
        super().__init__(D)
        self.my_scope = scope.ScopeObject(scope.top_scope)
    
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = self.my_scope
        scope.current_func_name =  self['identifier'].data

        if 'type' in self:
            if ('type' not in self['type']):
                scope.current_func_type = self['type']['base_type'].data
            else:
                raise NotImplementedError("Function with generic return type")
            
            return_is_statisfied = False
            func_type = self['type'].to_code()
        else:
            return_is_statisfied = True     # No need to return a value anywhere
            func_type = 'void'
        func_name = 'sn_' + self['identifier'].data
        func_parameters = ', '.join([x.to_code() for x in self['function_parameters']])

        statements, return_is_statisfied = StatementNode.process_statements(node=self['statements'], indent=newindent, satisfied=return_is_statisfied)
        
        if not return_is_statisfied:
            raise scope.SereneTypeError(f"Function '{self['identifier'].data}' is missing a return value in at least one execution path.")

        if (statements != ''):
            code = f'{func_type} {func_name}({func_parameters}) {{\n{newindent}{statements}{oldindent}}}'
        else:
            code = f'{func_type} {func_name}({func_parameters}) {{\n\n{oldindent}}}'

        indent_level -= 1
        scope.currentscope = scope.currentscope.parent

        scope.current_func_name = None  # For now, function definitions cannot be nested
        scope.current_func_type = None

        return code

class FunctionParameterNode(Node):
    # Function parameters need to be processed before other code so that function calls can be verified regardless of the order that functions are defined
    def __init__(self, D):
        super().__init__(D)
        
        code = self['type'].to_code()
        if 'accessor' in self:
            accessor = self['accessor'].data
            if accessor == 'mutate':
                code += '&'
        else:
            accessor = 'look'
        var_name = 'sn_' + self['identifier'].data
        code += ' ' + var_name

        if len(self['type'].data) == 1 and self['type']['base_type'].data in ('String', 'Char', 'Int', 'Float', 'Bool'):
            my_type = self['type']['base_type'].data
        else:
            raise NotImplementedError(self['type']['base_type'].data)

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.currentscope.add_binding(scope.ParameterObject(var_name, accessor, my_type))

        self.code = code
    
    def to_code(self):
        return self.code

class TypeNode(Node):
    def to_code(self):
        base = self['base_type'].data
        if base == 'Int':
            code = 'int64_t'
        elif base == 'Bool':
            code = 'bool'
        elif base == 'String':
            code = 'std::string'
        elif base == 'String':
            code = 'char'
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
    def process_statements(node, indent, satisfied):
        statement_list = []
        return_is_statisfied = satisfied
        for x in node:
            statement_list.append(x.to_code())
            if (not return_is_statisfied) and (x.satisfies_return):
                return_is_statisfied = True

        return indent.join(statement_list), return_is_statisfied

    def to_code(self):
        scope.line_number = self[0].data
        code = self[1].to_code()
        self.satisfies_return = self[1].satisfies_return if hasattr(self[1], 'satisfies_return') else False
        return code

class VarStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        expr_code = self['expression'].to_code()
        expr_type = self['expression'].get_type()
        if expr_type == 'Number':
            expr_type = 'Int'

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=True, var_type=expr_type))
        return f'auto {var_name} = {expr_code};\n'

class ConstStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        expr_code = self['expression'].to_code()
        expr_type = self['expression'].get_type()
        if expr_type == 'Number':
            expr_type = 'Int'

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=False, var_type=expr_type))
        return f'const auto {var_name} = {expr_code};\n'

class SetStatement(Node):
    def to_code(self):
        var_name = 'sn_' + self['identifier'].data

        if scope.currentscope.check_set(var_name):
            assign_op = self['assignment_op'].data
            expr_code = self['expression'].to_code()
            expr_type = self['expression'].get_type()

            correct_type = scope.currentscope.get_type_of(var_name)
            if expr_type != correct_type:
                raise scope.SereneTypeError(f"Incorrect type for assignment to variable '{self['identifier'].data}' at line number {scope.line_number}. Correct type is '{correct_type}'.")

            return f'{var_name} {assign_op} {expr_code};\n'
        else:
            if scope.currentscope.check_read(var_name):
                raise scope.SereneScopeError(f"Variable '{self['identifier'].data}' cannot be mutated at line number {scope.line_number}.")
            else:
                raise scope.SereneScopeError(f"Variable '{self['identifier'].data}' is not defined at line number {scope.line_number}.")

class PrintStatement(Node):
    def to_code(self):
        expr_code = [x.to_code() for x in self]
        expr_code.append('std::endl;\n')
        return 'std::cout << ' + ' << '.join(expr_code)

class RunStatement(Node):
    def to_code(self):
        return self['term'].to_code() + ';\n'

class ReturnStatement(Node):
    def __init__(self, D):
        super().__init__(D)
        self.satisfies_return = True
    
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
    def get_type(self):
        if (self.count("term") > 1):
            raise NotImplementedError("get_type() for ExpressionNode with infix operators")
        return self['term'].get_type()
    
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
                    var_name = self.var_to_access[3:]
                    raise scope.SereneScopeError(f"Variable '{var_name}' cannot be passed with accessor '{enclosing_accessor}' at line number {scope.line_number}.")

        return code

class TermNode(Node):
    def get_type(self):
        if len(self.data) > 1:
            raise NotImplementedError
        return self['base_expression'].get_type()
    
    def to_code(self):
        base_expr = self[0]
        inner_expr = base_expr[0]

        if inner_expr.nodetype == 'identifier':
            self.is_temporary = False
            code = base_expr.to_code()      # This is a bit redundant, but it's done to check read access on the identifier
            self.var_to_access = code
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
                            var_name = self.var_to_access[3:]
                            raise scope.SereneScopeError(f"Mutating methods cannot be called on variable '{var_name}' at line number {scope.line_number}.")
                    # Method calls return temporary values, so only the first method call in a term needs to be scope-checked
                    self.is_temporary = True
                code += x.to_code()
            elif x.nodetype == 'index_call':
                code += '[' + x['expression'].to_code() + ']'
        return code

class BaseExpressionNode(Node):
    def get_type(self):
        if 'literal' in self:
            if 'int_literal' in self['literal']:
                return 'Int'
            elif 'float_literal' in self['literal']:
                return 'Float'
            elif 'bool_literal' in self['literal']:
                return 'Bool'
            elif 'string_literal' in self['literal']:
                return 'String'
            elif 'char_literal' in self['literal']:
                return 'Char'
            else:
                raise NotImplementedError
        elif 'identifier' in self:
            var_name = 'sn_' + self['identifier'].data
            return scope.currentscope.get_type_of(var_name)
        elif 'function_call' in self:
            for y in scope.functions:
                if self['function_call']['identifier'].data == y['identifier'].data:
                    break
            original_function = y
            if 'type' not in original_function:
                raise scope.SereneTypeError(f"Function '{self['function_call']['identifier'].data}' with no return value cannot be used as an expression at line number {scope.line_number}.")
            if 'type' not in original_function['type']:
                return original_function['type']['base_type'].data
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError
        
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
                raise scope.SereneScopeError(f"Variable '{self['identifier'].data}' is not defined at line number {scope.line_number}.")
        elif 'literal' in self:
            if 'bool_literal' in self['literal']:
                return self['literal'][0].data.lower()
            else:
                return self['literal'][0].data
        elif 'expression' in self:
            return '(' + self['expression'].to_code() + ')'

class FunctionCallNode(Node):
    def to_code(self):
        if self['identifier'].data not in scope.function_names:
            raise scope.SereneScopeError(f"Function '{self['identifier'].data}' is not defined at line number {scope.line_number}.")
        code = 'sn_' + self['identifier'].data + '('

        num_called_params = len(self['function_call_parameters'].data) if type(self['function_call_parameters'].data) == NodeMap else 0
        for y in scope.functions:
            if self['identifier'].data == y['identifier'].data:
                break
        original_function = y

        if type(original_function['function_parameters'].data) != NodeMap:
            num_original_params = 0
        else:
            num_original_params = len(original_function['function_parameters'].data)
        if num_called_params > num_original_params:
            raise scope.SereneScopeError(f"Function '{self['identifier'].data}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < num_original_params:
            raise scope.SereneScopeError(f"Function '{self['identifier'].data}' is given too few parameters when called at line number {scope.line_number}.")

        params = []
        for i in range(num_called_params):
            o_param = original_function['function_parameters'][i]
            if 'accessor' in o_param:
                o_accessor = o_param['accessor'].data
            else:
                o_accessor = 'look'
            
            o_type = original_function.my_scope.get_type_of('sn_' + o_param['identifier'].data)
            
            c_param = self['function_call_parameters'][i]
            
            params.append(c_param.to_code(original_accessor = o_accessor, original_type = o_type, function_name = self['identifier'].data, param_name = o_param['identifier'].data))

        code += ', '.join(params) + ')'
        return code

class MethodCallNode(Node):
    def to_code(self):
        code = '.sn_' + self['identifier'].data + '('
        params = []
        for x in self['function_call_parameters']:
            raise NotImplementedError
            # params.append(x.to_code())  # This doesn't work anymore
        code += ', '.join(params) + ')'
        return code

class FunctionCallParameterNode(Node):
    def to_code(self, original_accessor, original_type, function_name, param_name):
        if 'accessor' in self:
            my_accessor = self['accessor'].data
        else:
            my_accessor = 'look'
        
        code = self['expression'].to_code(enclosing_accessor=my_accessor) # This will raise exceptions for incorrect accesses

        if (not self['expression'].is_temporary) and (my_accessor != original_accessor) and (my_accessor != 'copy'):
            raise scope.SereneScopeError(f"Function '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")

        if original_type != self['expression'].get_type():
            raise scope.SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to function '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")

        return code

class ForLoopNode(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)

        loopvar = 'sn_' + self['identifier'].data
        scope.currentscope.add_binding(scope.VariableObject(loopvar, mutable=False))

        if self.count('expression') == 2:   # start and endpoint
            startval = self[1].to_code()
            endval = self[2].to_code()
            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous two lines due to the side effects
            code = f'for (int {loopvar} = {startval}; {loopvar} < {endval}; {loopvar}++) {{\n{newindent}{statements}{oldindent}}}\n'
        else:
            myrange = self['expression'].to_code()
            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous line due to the side effects
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

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)

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

        return_satisfaction_list = []

        code = ''
        cur = self['if_branch']
        statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent, satisfied=False)
        return_satisfaction_list.append(return_is_statisfied)

        condition = cur['expression'].to_code()
        code += f'if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        scope.currentscope = scope.currentscope.parent

        if 'else_branch' in self:
            bound_elseif = len(self.data) - 1
        else:
            bound_elseif = len(self.data)
        
        for i in range(1, bound_elseif):
            scope.currentscope = scope.ScopeObject(scope.currentscope)

            cur = self[i]
            statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent, satisfied=False)
            return_satisfaction_list.append(return_is_statisfied)

            condition = cur['expression'].to_code()
            code += f'{oldindent}else if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        if 'else_branch' in self:
            scope.currentscope = scope.ScopeObject(scope.currentscope)

            cur = self['else_branch']
            statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent, satisfied=False)
            return_satisfaction_list.append(return_is_statisfied)

            code += f'{oldindent}else {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        indent_level -= 1

        self.satisfies_return = all(return_satisfaction_list) and ('else_branch' in self)

        return code

class MatchBlock(Node):
    def to_code(self):
        global indent_level
        oldindent = ('    '*indent_level)
        indent_level += 1
        newindent = ('    '*indent_level)

        subject = self['expression'].to_code()
        subject_type = self['expression'].get_type()
        branches = []
        for x in self:
            if x.nodetype == 'match_branch':
                scope.currentscope = scope.ScopeObject(scope.currentscope)
                
                if 'expression' in x:
                    conditions = []
                    for i in range(len(x.data) - 1):    # skip last element, which is 'statements'; all others are expressions
                        conditions.append('(' + x[i].to_code() + ' == ' + subject + ')')
                        expr_type = x[i].get_type()
                        if expr_type != subject_type:
                            raise scope.SereneTypeError(f"Incorrect type in match statement at line number {scope.line_number}. Type must match subject of type '{subject_type}'.")
                    
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
