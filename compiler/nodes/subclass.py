from __future__ import annotations
import scope
import nodes

indent_level = 0

# Functions ___________________________________________________________________

def add_indent():
    global indent_level
    oldindent = ('    '*indent_level)
    indent_level += 1
    newindent = ('    '*indent_level)

    return newindent, oldindent

def sub_indent():
    global indent_level
    oldindent = ('    '*indent_level)
    indent_level -= 1
    newindent = ('    '*indent_level)

    return newindent, oldindent    

# Subclasses __________________________________________________________________

class FunctionNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.my_scope = scope.ScopeObject(scope.top_scope)
    
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = self.my_scope
        scope.current_func_name =  self.get_scalar('identifier')

        if 'type' in self:
            if ('type' not in self['type']):
                scope.current_func_type = self['type'].get_scalar('base_type')
            else:
                raise NotImplementedError("Function with generic return type")
            
            return_is_statisfied = False
            func_type = self['type'].to_code()
        else:
            return_is_statisfied = True     # No need to return a value anywhere
            func_type = 'void'
        func_name = self.get_scalar('identifier')
        func_parameters = ', '.join([x.to_code() for x in self['function_parameters']])

        statements, return_is_statisfied = StatementNode.process_statements(node=self['statements'], indent=newindent, satisfied=return_is_statisfied)
        
        if not return_is_statisfied:
            raise scope.SereneTypeError(f"Function '{self.get_scalar('identifier')}' is missing a return value in at least one execution path.")

        if (statements != ''):
            code = f'{func_type} sn_{func_name}({func_parameters}) {{\n{newindent}{statements}{oldindent}}}'
        else:
            code = f'{func_type} sn_{func_name}({func_parameters}) {{\n\n{oldindent}}}'

        sub_indent()
        scope.currentscope = scope.currentscope.parent

        scope.current_func_name = None  # For now, function definitions cannot be nested
        scope.current_func_type = None

        return code

class FunctionParameterNode(nodes.Node):
    # Function parameters need to be processed before other code so that function calls can be verified regardless of the order that functions are defined
    def __init__(self, D):
        super().__init__(D)
        
        code = self['type'].to_code()
        if 'accessor' in self:
            accessor = self.get_scalar('accessor')
            if accessor == 'mutate':
                code += '&'
        else:
            accessor = 'look'
        var_name = self.get_scalar('identifier')
        code += ' ' + 'sn_'+ var_name

        if len(self['type'].data) == 1 and self['type'].get_scalar('base_type') in ('String', 'Char', 'Int', 'Float', 'Bool'):
            my_type = self['type'].get_scalar('base_type')
        else:
            raise NotImplementedError(self['type']['base_type'].data)

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.currentscope.add_binding(scope.ParameterObject(var_name, accessor, my_type))

        self.code = code
    
    def to_code(self):
        return self.code

class TypeNode(nodes.Node):
    def to_code(self):
        base = self.get_scalar('base_type')
        mapping = {'Int':    'int64_t',
                   'Bool':   'bool',
                   'String': 'std::string',
                   'Float':  'double',
                   'Char':   'char',
                   'Vector': 'SN_Vector',
                   'Array':  'SN_Array',
                  }
        if base in mapping:
            code = mapping[base]
        else:
            raise NotImplementedError
        if 'type' in self:  # Generic type
            return code + '<' + self['type'].to_code() + '>'
        else:
            return code

class StatementNode(nodes.Node):
    @staticmethod
    def process_statements(node, indent, satisfied):
        statement_list = []
        return_is_statisfied = satisfied
        for x in node:
            statement_list.append(x.to_code())
            if (not return_is_statisfied) and (x.satisfies_return):
                return_is_statisfied = True

        return indent.join(statement_list), return_is_statisfied

    def to_code(self):
        scope.line_number = self.get_scalar(0)
        code = self[1].to_code()
        self.satisfies_return = self[1].satisfies_return if hasattr(self[1], 'satisfies_return') else False
        return code

class VarStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar('identifier')

        expr_code = self['expression'].to_code()
        expr_type = self['expression'].get_type()

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=True, var_type=expr_type))
        return f'auto sn_{var_name} = {expr_code};\n'

class ConstStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar('identifier')

        expr_code = self['expression'].to_code()
        expr_type = self['expression'].get_type()

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=False, var_type=expr_type))
        return f'const auto sn_{var_name} = {expr_code};\n'

class SetStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar('identifier')

        if scope.currentscope.check_set(var_name):
            assign_op = self.get_scalar('assignment_op')
            expr_code = self['expression'].to_code()
            expr_type = self['expression'].get_type()

            correct_type = scope.currentscope.get_type_of(var_name)
            if expr_type != correct_type:
                raise scope.SereneTypeError(f"Incorrect type for assignment to variable '{self.get_scalar('identifier')}' at line number {scope.line_number}. Correct type is '{correct_type}'.")

            return f'sn_{var_name} {assign_op} {expr_code};\n'
        else:
            if scope.currentscope.check_read(var_name):
                raise scope.SereneScopeError(f"Variable '{var_name}' cannot be mutated at line number {scope.line_number}.")
            else:
                raise scope.SereneScopeError(f"Variable '{var_name}' is not defined at line number {scope.line_number}.")

class PrintStatement(nodes.Node):
    def to_code(self):
        expr_code = [x.to_code() for x in self]
        expr_code.append('std::endl;\n')
        return 'std::cout << ' + ' << '.join(expr_code)

class RunStatement(nodes.Node):
    def to_code(self):
        return self['term'].to_code() + ';\n'

class ReturnStatement(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.satisfies_return = True
    
    def to_code(self):
        expr_code = self['expression'].to_code()
        return f'return {expr_code};\n'

class BreakStatement(nodes.Node):
    def to_code(self):
        return 'break;\n'

class ContinueStatement(nodes.Node):
    def to_code(self):
        return 'continue;\n'

class ExpressionNode(nodes.Node):
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
                    code += ' ' + cur.get_scalar(0) + ' '
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
                    raise scope.SereneScopeError(f"Variable '{self.var_to_access}' cannot be passed with accessor '{enclosing_accessor}' at line number {scope.line_number}.")

        return code

class TermNode(nodes.Node):
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
            self.var_to_access = inner_expr.data
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
                code += '.sn_' + x.get_scalar('identifier')
            elif x.nodetype == 'method_call':
                if not self.is_temporary:
                    if 'mutate_method_symbol' in x:
                        if not scope.currentscope.check_pass(self.var_to_access, 'mutate'):
                            raise scope.SereneScopeError(f"Mutating methods cannot be called on variable '{self.var_to_access}' at line number {scope.line_number}.")
                    # Method calls return temporary values, so only the first method call in a term needs to be scope-checked
                    self.is_temporary = True
                code += x.to_code()
            elif x.nodetype == 'index_call':
                code += '[' + x['expression'].to_code() + ']'
        return code

class BaseExpressionNode(nodes.Node):
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
            var_name = self.get_scalar('identifier')
            return scope.currentscope.get_type_of(var_name)
        elif 'function_call' in self:
            for y in scope.functions:
                if self['function_call'].get_scalar('identifier') == y.get_scalar('identifier'):
                    break
            original_function = y
            if 'type' not in original_function:
                raise scope.SereneTypeError(f"Function '{self['function_call'].get_scalar('identifier')}' with no return value cannot be used as an expression at line number {scope.line_number}.")
            if 'type' not in original_function['type']:
                return original_function['type'].get_scalar('base_type')
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
            var_name = self.get_scalar('identifier')
            if scope.currentscope.check_read(var_name):     # If the variable also needs to be mutated/moved, that will already be checked within TermNode or ExpressionNode
                return 'sn_' + var_name
            else:
                raise scope.SereneScopeError(f"Variable '{var_name}' is not defined at line number {scope.line_number}.")
        elif 'literal' in self:
            if 'bool_literal' in self['literal']:
                return self['literal'].get_scalar(0).lower()
            else:
                return self['literal'].get_scalar(0)
        elif 'expression' in self:
            return '(' + self['expression'].to_code() + ')'

class FunctionCallNode(nodes.Node):
    def to_code(self):
        if self.get_scalar('identifier') not in scope.function_names:
            raise scope.SereneScopeError(f"Function '{self.get_scalar('identifier')}' is not defined at line number {scope.line_number}.")
        code = 'sn_' + self.get_scalar('identifier') + '('

        num_called_params = len(self['function_call_parameters'].data) if type(self['function_call_parameters'].data) == nodes.NodeMap else 0
        for y in scope.functions:
            if self.get_scalar('identifier') == y.get_scalar('identifier'):
                break
        original_function = y

        if type(original_function['function_parameters'].data) != nodes.NodeMap:
            num_original_params = 0
        else:
            num_original_params = len(original_function['function_parameters'].data)
        if num_called_params > num_original_params:
            raise scope.SereneScopeError(f"Function '{self.get_scalar('identifier')}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < num_original_params:
            raise scope.SereneScopeError(f"Function '{self.get_scalar('identifier')}' is given too few parameters when called at line number {scope.line_number}.")

        params = []
        for i in range(num_called_params):
            o_param = original_function['function_parameters'][i]
            if 'accessor' in o_param:
                o_accessor = o_param.get_scalar('accessor')
            else:
                o_accessor = 'look'
            
            o_type = original_function.my_scope.get_type_of(o_param.get_scalar('identifier'))
            
            c_param = self['function_call_parameters'][i]
            
            params.append(c_param.to_code(original_accessor = o_accessor, original_type = o_type, function_name = self.get_scalar('identifier'), param_name = o_param.get_scalar('identifier')))

        code += ', '.join(params) + ')'
        return code

class MethodCallNode(nodes.Node):
    def to_code(self):
        code = '.sn_' + self.get_scalar('identifier') + '('
        params = []
        for x in self['function_call_parameters']:
            raise NotImplementedError
            # params.append(x.to_code())  # This doesn't work anymore
        code += ', '.join(params) + ')'
        return code

class FunctionCallParameterNode(nodes.Node):
    def to_code(self, original_accessor, original_type, function_name, param_name):
        if 'accessor' in self:
            my_accessor = self.get_scalar('accessor')
        else:
            my_accessor = 'look'
        
        code = self['expression'].to_code(enclosing_accessor=my_accessor) # This will raise exceptions for incorrect accesses

        if (not self['expression'].is_temporary) and (my_accessor != original_accessor) and (my_accessor != 'copy'):
            raise scope.SereneScopeError(f"Function '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")

        if original_type != self['expression'].get_type():
            raise scope.SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to function '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")

        return code

class ForLoopNode(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)

        loopvar = self.get_scalar('identifier')
        scope.currentscope.add_binding(scope.VariableObject(loopvar, mutable=False))

        if self.count('expression') == 2:   # start and endpoint
            startval = self[1].to_code()
            endval = self[2].to_code()
            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous two lines due to the side effects
            code = f'for (int sn_{loopvar} = {startval}; sn_{loopvar} < {endval}; sn_{loopvar}++) {{\n{newindent}{statements}{oldindent}}}\n'
        else:
            myrange = self['expression'].to_code()
            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous line due to the side effects
            code = f'for (const auto& sn_{loopvar} : {myrange}) {{\n{newindent}{statements}{oldindent}}}\n'
        
        sub_indent()
        scope.currentscope = scope.currentscope.parent

        return code

class WhileLoopNode(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)

        statements = newindent.join([x.to_code() for x in self['statements']])
        condition = self['expression'].to_code()
        code = f'while ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        sub_indent()
        scope.currentscope = scope.currentscope.parent

        return code

class IfBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

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
        
        sub_indent()

        self.satisfies_return = all(return_satisfaction_list) and ('else_branch' in self)

        return code

class MatchBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

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
        sub_indent()
        return (f'{oldindent}else ').join(branches)
