from __future__ import annotations
from typing import Type
import typecheck
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

def get_cpp_type(my_type):
    assert type(my_type) == typecheck.TypeObject
    base = my_type.base
    mapping = {'Int':    'int64_t',
               'Bool':   'bool',
               'String': 'std::string',
               'Float':  'double',
               'Char':   'char',
               'Vector': 'SN_Vector',
               'Array':  'SN_Array',
              }
    if base in mapping:
        cpp_type = mapping[base]
    else:
        raise NotImplementedError
    if my_type.params is None:
        return cpp_type
    else:  # Generic type
        return cpp_type + '<' + get_cpp_type(my_type.params[0]) + '>'

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
                scope.current_func_type = self['type'].get_type()
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
            my_type = typecheck.TypeObject(self['type'].get_scalar('base_type'))
        else:
            if self['type'].get_scalar('base_type') in ('Vector', 'Array'):
                if len(self['type']['type'].data) == 1 and self['type']['type'].get_scalar('base_type') in ('String', 'Char', 'Int', 'Float', 'Bool'):
                    my_type = typecheck.TypeObject(self['type'].get_scalar('base_type'), params=[typecheck.TypeObject(self['type']['type'].get_scalar('base_type'))])
            else:
                raise NotImplementedError(self['type']['base_type'].data)

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.currentscope.add_binding(scope.ParameterObject(var_name, accessor, my_type))

        self.code = code
    
    def to_code(self):
        return self.code

class TypeNode(nodes.Node):
    def get_type(self):
        base = self['base_type'].data
        num_generic_params = self.count('type')
        if num_generic_params == 0:
            return typecheck.TypeObject(base)
        elif num_generic_params == 1:
            return typecheck.TypeObject(base, [self['type'].get_type()])
        else:
            raise NotImplementedError

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
    def process_statements(node, indent, satisfied=False):
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

        if 'type' in self:
            written_type = self['type'].get_type()
            if written_type != expr_type:
                raise scope.SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=True, var_type=expr_type))

        cpp_type = get_cpp_type(expr_type)
        return f'{cpp_type} sn_{var_name} = {expr_code};\n'

class ConstStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar('identifier')

        expr_code = self['expression'].to_code()
        expr_type = self['expression'].get_type()

        if 'type' in self:
            written_type = self['type'].get_type()
            if written_type != expr_type:
                raise scope.SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")

        scope.currentscope.add_binding(scope.VariableObject(var_name, mutable=False, var_type=expr_type))

        cpp_type = get_cpp_type(expr_type)
        return f'const {cpp_type} sn_{var_name} = {expr_code};\n'

class SetStatement(nodes.Node):
    def to_code(self):
        if 'place_term' in self:
            if self['place_term']['base_expression'][0].nodetype != 'identifier':
                raise scope.SereneTypeError(f"Invalid expression for left-hand side of 'set' statement at line number {scope.line_number}.")
            var_name = self['place_term']['base_expression'].get_scalar('identifier')
            lhs_code = self['place_term'].to_code()
            correct_type = self['place_term'].get_type()
        else:
            var_name = self.get_scalar('identifier')
            lhs_code = 'sn_' + var_name
            correct_type = scope.currentscope.get_type_of(var_name)

        if scope.currentscope.check_set(var_name):
            expr_code = self['expression'].to_code()
            expr_type = self['expression'].get_type()

            if expr_type != correct_type:
                raise scope.SereneTypeError(f"Incorrect type for assignment to variable '{self.get_scalar('identifier')}' at line number {scope.line_number}. Correct type is '{correct_type}'.")

            assign_op = self.get_scalar('assignment_op')
            return f'{lhs_code} {assign_op} {expr_code};\n'
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
        if type(self.data) == nodes.NodeMap:
            self.satisfies_return = True
        else:
            self.satisfies_return = False   # "return" without value
    
    def to_code(self):
        if type(self.data) == nodes.NodeMap:
            expr_code = self['expression'].to_code()
            if scope.current_func_type is None:
                raise scope.SereneTypeError(f"Cannot return value from function with no return type at line number {scope.line_number}.")
            if self['expression'].get_type() != scope.current_func_type:
                raise scope.SereneTypeError(f"Incorrect type for return statement at line number {scope.line_number}.")
            return f'return {expr_code};\n'
        else:
            if scope.current_func_type is not None:
                raise scope.SereneTypeError(f"Return statement at line number {scope.line_number} has no value.")
            return 'return;\n'

class BreakStatement(nodes.Node):
    def to_code(self):
        if len(scope.loops) > 0:
            return 'break;\n'
        else:
            raise scope.SereneScopeError(f"'break' cannot be used outside of a loop at line number {scope.line_number}.")

class ContinueStatement(nodes.Node):
    def to_code(self):
        if len(scope.loops) > 0:
            self.satisfies_return = scope.loops[-1].is_infinite
            return 'continue;\n'
        else:
            raise scope.SereneScopeError(f"'continue' cannot be used outside of a loop at line number {scope.line_number}.")

class ExpressionNode(nodes.Node):
    def get_type(self):
        if (self.count("term") > 1):
            this_type = None
            for x in self:
                if x.nodetype != "term":
                    continue
                if this_type is None:
                    this_type = x.get_type()
                else:
                    if x.get_type() != this_type:
                        raise scope.SereneTypeError(f"Mismatching types for infix operator(s) at line number {scope.line_number}.")
            return this_type
        else:
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
    def get_type_sequence(self):
        L = []
        base_type = self[0].get_type()
        L.append(base_type)
        if len(self.data) > 1:
            for i in range(1, len(self.data)):
                cur = self[i]
                prev = self[i-1]
                prev_type = L[-1]
                if prev_type.base in typecheck.standard_types:
                    orig_type = typecheck.standard_types[prev_type.base]
                    if cur.nodetype == 'field_access':
                        field_name = cur['identifier'].data
                        if field_name in orig_type.members:
                            member_type = orig_type.members[field_name]
                            if type(member_type) == str:
                                L.append(typecheck.TypeObject(member_type))
                            else:
                                raise NotImplementedError   # Member with generic type
                        else:
                            raise scope.SereneTypeError(f"Invalid field access in expression at line number {scope.line_number}.")
                    elif cur.nodetype == 'method_call':
                        method_name = cur['identifier'].data
                        if method_name in orig_type.methods:
                            method_return_type = orig_type.methods[method_name][0]
                            if type(method_return_type) == str:
                                if method_return_type == '':
                                    if i + 1 == len(self.data):
                                        L.append(None)
                                    else:
                                        raise NotImplementedError
                                L.append(typecheck.TypeObject(method_return_type))
                            else:
                                raise NotImplementedError   # Member with generic type
                    elif cur.nodetype == 'index_call':
                        if prev_type.base in ('Vector', 'Array') and prev_type.params[0].params is None:
                            if self['index_call']['expression'].get_type().base != 'Int':
                                raise scope.SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
                            L.append(typecheck.TypeObject(prev_type.params[0].base))
                        elif prev_type.base == 'String':
                            if self['index_call']['expression'].get_type().base != 'Int':
                                raise scope.SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
                            L.append(typecheck.TypeObject('Char'))
                    else:
                        raise NotImplementedError
                else:
                    raise scope.SereneTypeError(f"Unknown type in expression at line number {scope.line_number}")

        return L
    
    def get_type(self):
        this_type = self.get_type_sequence()[-1]
        if this_type is None:
            raise scope.SereneTypeError(f"Unknown type in expression at line number {scope.line_number}")
        else:
            return this_type
    
    def to_code(self):
        base_expr = self[0]
        inner_expr = base_expr[0]

        if len(self.data) > 1:
            type_seq = self.get_type_sequence()

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
            current_type = type_seq[i-1]
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
                if current_type is None:
                    raise NotImplementedError
                else:
                    if current_type.base in ('Vector', 'Array') and current_type.params[0].params is None:
                        code += x.to_code(on_type=current_type)
                    elif current_type.base == "String" and current_type.params is None:
                        code += x.to_code(on_type=current_type)
                    else:
                        raise NotImplementedError
            elif x.nodetype == 'index_call':
                code += '[' + x['expression'].to_code() + ']'
            else:
                raise NotImplementedError
        return code

class PlaceTermNode(TermNode):  # Identical to TermNode, except with no method calls (prevented in the parsing stage). Used for 'set' statements
    pass

class BaseExpressionNode(nodes.Node):
    def get_type(self):
        if 'literal' in self:
            if 'int_literal' in self['literal']:
                return typecheck.TypeObject('Int')
            elif 'float_literal' in self['literal']:
                return typecheck.TypeObject('Float')
            elif 'bool_literal' in self['literal']:
                return typecheck.TypeObject('Bool')
            elif 'string_literal' in self['literal']:
                return typecheck.TypeObject('String')
            elif 'char_literal' in self['literal']:
                return typecheck.TypeObject('Char')
            else:
                raise NotImplementedError
        elif 'expression' in self:
            return self['expression'].get_type()
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
                return typecheck.TypeObject(original_function['type'].get_scalar('base_type'))
            else:
                raise NotImplementedError
        elif 'constructor_call' in self:
            return self['constructor_call'].get_type()
        else:
            raise NotImplementedError
        
    def to_code(self):
        if 'function_call' in self:
            return self['function_call'].to_code()
        elif 'constructor_call' in self:
            return self['constructor_call'].to_code()
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
    def to_code(self, on_type):
        method_name = self.get_scalar('identifier')
        if on_type.base in typecheck.standard_types:
            orig_type = typecheck.standard_types[on_type.base]
            if 'mutate_method_symbol' in self:
                full_method_name = method_name + '!'
            else:
                full_method_name = method_name
            if full_method_name not in orig_type.methods:
                raise scope.SereneTypeError(f"Method '{method_name}' does not exist at line number {scope.line_number}.")
        else:
            raise scope.SereneTypeError(f"Method '{method_name}' does not exist at line number {scope.line_number}.")
        code = '.sn_' + method_name + '('

        params = []
        orig_params = orig_type.methods[full_method_name][1]
        num_called_params = len(self['function_call_parameters'].data)

        if num_called_params > len(orig_params):
            raise scope.SereneScopeError(f"Method '{method_name}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < len(orig_params):
            raise scope.SereneScopeError(f"Function '{method_name}' is given too few parameters when called at line number {scope.line_number}.")

        for i in range(num_called_params):
            orig_param = orig_params[i]
            orig_accessor = orig_param.accessor
            
            orig_type = orig_param.var_type
            if isinstance(orig_type, typecheck.TypeVar):
                if on_type.base in ('Vector', 'Array') and on_type.params[0].params is None:
                    orig_type = typecheck.TypeObject(on_type.params[0].base)
                else:
                    raise NotImplementedError
            
            c_param = self['function_call_parameters'][i]
            
            params.append(c_param.to_code(original_accessor = orig_accessor, original_type = orig_type, function_name = method_name, param_name = orig_param.name, method=True))

        code += ', '.join(params) + ')'
        return code

class ConstructorCallNode(nodes.Node):
    def get_type(self):
        if self.get_scalar("base_type") == 'Array':
            if len(self['constructor_call_parameters'].data) >= 1 and self['constructor_call_parameters'][0][0].nodetype == 'expression':
                return typecheck.TypeObject(base='Array', params=[self['constructor_call_parameters'][0][0].get_type()])
            else:
                raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")        
        elif self.get_scalar("base_type") == 'Vector':
            if len(self['constructor_call_parameters'].data) == 1 and self['constructor_call_parameters'][0][0].nodetype == 'type':    # Vector(Int), Vector(String), etc.
                type_node = self['constructor_call_parameters'][0][0]
                if 'type' in type_node:
                    raise NotImplementedError
                return typecheck.TypeObject(base='Vector', params=[typecheck.TypeObject(base=type_node.get_scalar('base_type'))])
            elif len(self['constructor_call_parameters'].data) >= 1 and self['constructor_call_parameters'][0][0].nodetype == 'expression':
                return typecheck.TypeObject(base='Vector', params=[self['constructor_call_parameters'][0][0].get_type()])
            else:
                raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
        else:
            raise scope.SereneTypeError(f"Type constructor called at line number {scope.line_number} is not defined.")
    
    def to_code(self):
        if self.get_scalar("base_type") == 'Array':
            if len(self['constructor_call_parameters'].data) >= 1 and self['constructor_call_parameters'][0][0].nodetype == 'expression':
                elems = []
                elem_type = None
                for i in range(len(self['constructor_call_parameters'].data)):
                    cur = self['constructor_call_parameters'][i][0]
                    if cur.nodetype != 'expression':
                        raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                    elems.append(cur.to_code())
                    if elem_type is None:
                        elem_type = cur.get_type()
                    elif elem_type != cur.get_type():
                        raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                inner_code = '{' + ', '.join(elems) + '}'
                type_param = get_cpp_type(elem_type)
                return f"SN_Array<{type_param}>({inner_code})"
            else:
               raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.") 
        elif self.get_scalar("base_type") == 'Vector':
            if len(self['constructor_call_parameters'].data) == 1 and self['constructor_call_parameters'][0][0].nodetype == 'type':    # Vector(Int), Vector(String), etc.
                type_node = self['constructor_call_parameters'][0][0]
                if 'type' in type_node:
                    raise NotImplementedError
                type_param = get_cpp_type(typecheck.TypeObject(base=type_node.get_scalar('base_type')))
                return f"SN_Vector<{type_param}>()"
            elif len(self['constructor_call_parameters'].data) >= 1 and self['constructor_call_parameters'][0][0].nodetype == 'expression':
                elems = []
                elem_type = None
                for i in range(len(self['constructor_call_parameters'].data)):
                    cur = self['constructor_call_parameters'][i][0]
                    if cur.nodetype != 'expression':
                        raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                    elems.append(cur.to_code())
                    if elem_type is None:
                        elem_type = cur.get_type()
                    elif elem_type != cur.get_type():
                        raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                inner_code = '{' + ', '.join(elems) + '}'
                type_param = get_cpp_type(elem_type)
                return f"SN_Vector<{type_param}>({inner_code})"
            else:
                raise scope.SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                        
        else:
            raise scope.SereneTypeError(f"Type constructor called at line number {scope.line_number} is not defined.")
        

class FunctionCallParameterNode(nodes.Node):
    def to_code(self, original_accessor, original_type, function_name, param_name, method=False):
        if 'accessor' in self:
            my_accessor = self.get_scalar('accessor')
        else:
            my_accessor = 'look'
        
        code = self['expression'].to_code(enclosing_accessor=my_accessor) # This will raise exceptions for incorrect accesses

        if (not self['expression'].is_temporary) and (my_accessor != original_accessor) and (my_accessor != 'copy'):
            if method:
                raise scope.SereneScopeError(f"Method '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")
            else:
                raise scope.SereneScopeError(f"Function '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")

        if original_type != self['expression'].get_type():
            if method:
                raise scope.SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to method '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")
            else:
                raise scope.SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to function '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")

        return code

class ForLoopNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.is_infinite = False

    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)
        scope.loops.append(self)

        loopvar = self.get_scalar('identifier')
        

        if self.count('expression') == 2:   # start and endpoint
            var_type = self[1].get_type()
            if var_type != self[2].get_type():
                raise scope.SereneTypeError(f"Mismatching types in for-loop at line number {scope.line_number}.")
            scope.currentscope.add_binding(scope.VariableObject(loopvar, mutable=False, var_type=var_type))

            startval = self[1].to_code()
            endval = self[2].to_code()

            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous two lines due to the side effects
            code = f'for (int sn_{loopvar} = {startval}; sn_{loopvar} < {endval}; sn_{loopvar}++) {{\n{newindent}{statements}{oldindent}}}\n'
        else:
            expr_type = self['expression'].get_type()
            if expr_type.base in ('Array', 'Vector') and expr_type.params[0].params is None:
                var_type = expr_type.params[0].base
                scope.currentscope.add_binding(scope.VariableObject(loopvar, mutable=False, var_type=typecheck.TypeObject(var_type)))
            else:
                raise NotImplementedError
            
            myrange = self['expression'].to_code()
            statements = newindent.join([x.to_code() for x in self['statements']])  # This must be run AFTER the previous line due to the side effects
            cpp_type = get_cpp_type(typecheck.TypeObject(var_type))
            code = f'for (const {cpp_type}& sn_{loopvar} : {myrange}) {{\n{newindent}{statements}{oldindent}}}\n'
        
        sub_indent()
        scope.currentscope = scope.currentscope.parent
        assert(scope.loops.pop() is self)

        return code

class WhileLoopNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)

        condition_is_true = False   # check for "while (True) ...", "while ((((True)))) ...", etc.
        cur = self['expression']
        while cur.count("term") == 1:
            if(len(cur["term"].data) == 1):
                term = cur["term"]
                base_expr = term["base_expression"]
                if base_expr[0].nodetype == "literal":
                    if base_expr[0][0].nodetype == "bool_literal" and base_expr[0].get_scalar("bool_literal") == "True":
                        condition_is_true = True
                        break
                elif base_expr[0].nodetype == "expression":
                    cur = base_expr[0]
                    continue
            break

        self.is_infinite = condition_is_true

    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = scope.ScopeObject(scope.currentscope, loop=True)
        scope.loops.append(self)

        statements, return_is_statisfied = StatementNode.process_statements(node=self['statements'], indent=newindent)
        condition = self['expression'].to_code()
        code = f'while ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        sub_indent()
        self.satisfies_return = self.is_infinite and return_is_statisfied

        scope.currentscope = scope.currentscope.parent
        assert(scope.loops.pop() is self)

        return code

class IfBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.currentscope = scope.ScopeObject(scope.currentscope)

        return_satisfaction_list = []

        code = ''
        cur = self['if_branch']
        statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent)
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
            statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent)
            return_satisfaction_list.append(return_is_statisfied)

            condition = cur['expression'].to_code()
            code += f'{oldindent}else if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        if 'else_branch' in self:
            scope.currentscope = scope.ScopeObject(scope.currentscope)

            cur = self['else_branch']
            statements, return_is_statisfied = StatementNode.process_statements(node=cur['statements'], indent=newindent)
            return_satisfaction_list.append(return_is_statisfied)

            code += f'{oldindent}else {{\n{newindent}{statements}{oldindent}}}\n'

            scope.currentscope = scope.currentscope.parent
        
        sub_indent()

        self.satisfies_return = all(return_satisfaction_list) and ('else_branch' in self)

        return code

class MatchBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        return_satisfaction_list = []
        has_else = False

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
                        statements, return_is_statisfied = StatementNode.process_statements(node=x['statements'], indent=newindent)
                    else:
                        statements = x['statement'].to_code()
                        return_is_statisfied = x['statement'].satisfies_return
                    branchcode = f'if ({conditions}) {{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                else:   # 'else' branch in 'match' block
                    has_else = True
                    if 'statements' in x:
                        statements, return_is_statisfied = StatementNode.process_statements(node=x['statements'], indent=newindent)
                    else:
                        statements = x['statement'].to_code()
                        return_is_statisfied = x['statement'].satisfies_return
                    branchcode = f'{{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                
                return_satisfaction_list.append(return_is_statisfied)
                scope.currentscope = scope.currentscope.parent
        sub_indent()
        self.satisfies_return = all(return_satisfaction_list) and has_else
        return (f'{oldindent}else ').join(branches)
