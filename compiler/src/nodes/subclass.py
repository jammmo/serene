from __future__ import annotations
from typing import Type

from src.common import *
from src import typecheck, scope, nodes

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
               'String': 'SN_String',
               'Float':  'double',
               'Char':   'char',
               'Vector': 'SN_Vector',
               'Array':  'SN_Array',
              }
    if base in mapping:
        cpp_type = mapping[base]
        if my_type.params is None:
            return cpp_type
        else:  # Generic type
            return cpp_type + '<' + get_cpp_type(my_type.params[0]) + '>'
    elif base in typecheck.user_defined_types:
        return f"SN_{base}"
    else:
        raise SereneTypeError(f"Unknown type: {my_type}.")

# Utilities ___________________________________________________________________
class UnreachableError(Exception):
    # UnreachableErrors are usually a sign of a bug (likely a change in the parser code that has not been accounted for in the compiler).
    # Compare with NotImplementedError, which is used here for known future features that have not yet been implemented.
    pass

# Subclasses __________________________________________________________________

class FunctionNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.my_scope = scope.ScopeObject(scope.top_scope)
    
    def to_forward_declaration(self):
        scope.scope_for_setup = self.my_scope
        for x in self[Symbol.function_parameters]:
            x.setup()

        if Symbol.type in self:
            func_type = self[Symbol.type].to_code()  # C++ return type        
        else:
            func_type = 'void'
        func_name = self.get_scalar(Symbol.identifier)
        func_parameters = ', '.join([x.to_code() for x in self[Symbol.function_parameters]])

        code = f'{func_type} sn_{func_name}({func_parameters});'

        return code
    
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = self.my_scope

        if Symbol.type in self:
            scope.current_func_type = self[Symbol.type].get_type()
            func_type = self[Symbol.type].to_code()  # C++ return type
            return_is_statisfied = False            
        else:
            func_type = 'void'
            return_is_statisfied = True     # No need to return a value anywhere            
        func_name = self.get_scalar(Symbol.identifier)
        func_parameters = ', '.join([x.to_code() for x in self[Symbol.function_parameters]])

        statements, return_is_statisfied = StatementNode.process_statements(node=self[Symbol.statements], indent=newindent, satisfied=return_is_statisfied)
        
        if not return_is_statisfied:
            raise SereneTypeError(f"Function '{self.get_scalar(Symbol.identifier)}' is missing a return value in at least one execution path.")

        if (statements != ''):
            code = f'{oldindent}{func_type} sn_{func_name}({func_parameters}) {{\n{newindent}{statements}{oldindent}}}'
        else:
            code = f'{oldindent}{func_type} sn_{func_name}({func_parameters}) {{\n\n{oldindent}}}'

        sub_indent()
        scope.current_scope = scope.current_scope.parent
        scope.current_func_type = None

        return code

class MethodDefinitionNode(nodes.Node):
    def to_tuple_description(self, parent_scope):
        # Should be used while struct definitions are being processed and before method definitions are processed (as it calls FunctionParameterNode.setup)
        
        # return tuple similar to ("delete!", ("", [scope.ParameterObject('index', 'look', TypeObject('Int'))]))

        parameter_list = []
        self.my_scope = scope.ScopeObject(parent=parent_scope)
        scope.scope_for_setup = self.my_scope
        for x in self[Symbol.function_parameters]:
            x.setup()
            parameter_list.append(scope.scope_for_setup[x.get_scalar(Symbol.identifier)])

        if Symbol.type in self:
            func_type = self[Symbol.type].get_type()
            if func_type.params is not None:
                raise NotImplementedError
        else:
            func_type = None
        
        func_name = self.get_scalar(Symbol.identifier)
        if Symbol.mutate_method_symbol in self:
            func_name = func_name + '!'
        
        return (func_name, (func_type, parameter_list))

    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = self.my_scope

        if Symbol.type in self:
            scope.current_func_type = self[Symbol.type].get_type()
            func_type = self[Symbol.type].to_code()  # C++ return type
            return_is_statisfied = False
        else:
            func_type = 'void'
            return_is_statisfied = True     # No need to return a value anywhere
        func_name = self.get_scalar(Symbol.identifier)
        func_parameters = ', '.join([x.to_code() for x in self[Symbol.function_parameters]])

        statements, return_is_statisfied = StatementNode.process_statements(node=self[Symbol.statements], indent=newindent, satisfied=return_is_statisfied)

        if not return_is_statisfied:
            raise SereneTypeError(f"Method '{self.get_scalar(Symbol.identifier)}' is missing a return value in at least one execution path.")

        if (statements != ''):
            code = f'{oldindent}{func_type} sn_{func_name}({func_parameters}) {{\n{newindent}{statements}{oldindent}}}'
        else:
            code = f'{oldindent}{func_type} sn_{func_name}({func_parameters}) {{\n\n{oldindent}}}'

        sub_indent()
        scope.current_scope = scope.current_scope.parent
        scope.current_func_type = None

        return code

class FunctionParameterNode(nodes.Node):
    # Function parameters need to be processed before other code so that function calls can be verified regardless of the order that functions are defined.
    # However, they need access to struct definitions, so the setup() function is called when forward declarations are created, which is before the function bodies are processed.
    def setup(self):
        code = self[Symbol.type].to_code()
        if Symbol.accessor in self:
            accessor = self.get_scalar(Symbol.accessor)
        else:
            accessor = 'look'
        
        if accessor == 'look':
            code += ' const&'
        elif accessor == 'mutate':
            code += '&'
        elif accessor == 'move':
            code += '&&'
        # When accessor is 'copy', the default pass-by-value behavior in C++ is correct, so no additional modifiers are needed

        var_name = self.get_scalar(Symbol.identifier)
        code += ' ' + 'sn_'+ var_name

        base_type = self[Symbol.type].get_scalar(Symbol.base_type)
        L = [base_type]

        cur = self[Symbol.type]
        while Symbol.type in cur:
            if base_type not in ('Vector', 'Array'):
                if base_type in typecheck.user_defined_types:
                    raise SereneTypeError(f"Unnecessary type parameter specified for non-generic type '{base_type}'.")
                else:
                    raise SereneTypeError(f"Unknown generic type: {base_type}.")
                               
            cur = cur[Symbol.type]
            base_type = cur.get_scalar(Symbol.base_type)

            L.append(base_type)
        
        def get_my_type(i):
            if i == len(L)-1:
                return typecheck.TypeObject(L[i])
            else:
                return typecheck.TypeObject(L[i], params=[get_my_type(i+1)])
        
        my_type = get_my_type(0)

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.scope_for_setup.add_persistent_binding(scope.ParameterObject(var_name, accessor, my_type))
        self.code = code
    
    def to_code(self):
        return self.code

class TypeNode(nodes.Node):
    def get_type(self):
        base = self[Symbol.base_type].data
        num_generic_params = self.count(Symbol.type)
        if num_generic_params == 0:
            return typecheck.TypeObject(base)
        elif num_generic_params == 1:
            return typecheck.TypeObject(base, [self[Symbol.type].get_type()])
        else:
            raise UnreachableError

    def to_code(self):
        return get_cpp_type(self.get_type())

class StatementNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.read_list = []     # Any variable that will be accessed with look or copy
        self.write_list = []    # Any variable that will be accessed with mutate or move
        self.delete_list = []   # Any variable that will be accessed with move
        # These lists contain tuples of (variable as ParameterObject or VariableObject, field_name1, field_name2, ...)
    
    @staticmethod
    def process_statements(node, indent, satisfied=False, bindings_to_delete=None):
        statement_list = []
        return_is_statisfied = satisfied
        if bindings_to_delete is not None:
            bindings_to_restore = []
        for x in node:
            if bindings_to_delete is not None:
                x.bindings_to_restore = bindings_to_restore
            statement_list.append(x.to_code())
            if (not return_is_statisfied) and (x.satisfies_return):
                return_is_statisfied = True

        if bindings_to_delete is not None:
            for s, binding in bindings_to_restore:
                s.add_binding(binding)
                bindings_to_delete.append((s, binding.name))
            
            bindings_to_restore.clear()
            
        return indent.join(statement_list), return_is_statisfied

    def to_code(self):
        scope.line_number = self.get_scalar(0)
        scope.current_statement = self
        scope.current_enclosure = self
        code = self[1].to_code()
        self.satisfies_return = self[1].satisfies_return if hasattr(self[1], 'satisfies_return') else False
        if type(scope.current_statement) != StatementNode:
            raise TypeError
        if scope.current_statement == self:     # Ignore statements that contain other statements
            if hasattr(self, 'bindings_to_restore'):
                scope.current_scope.check_all_statement_accesses(bindings_to_restore=self.bindings_to_restore)
            else:
                scope.current_scope.check_all_statement_accesses()
        return code

class VarStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar(Symbol.identifier)

        expr_code = self[Symbol.expression].to_code()
        expr_type = self[Symbol.expression].get_type()

        if Symbol.type in self:
            written_type = self[Symbol.type].get_type()
            if written_type != expr_type:
                raise SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")

        scope.current_scope.add_binding(scope.VariableObject(var_name, mutable=True, var_type=expr_type))

        cpp_type = get_cpp_type(expr_type)
        return f'{cpp_type} sn_{var_name} = {expr_code};\n'

class ConstStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar(Symbol.identifier)

        expr_code = self[Symbol.expression].to_code()
        expr_type = self[Symbol.expression].get_type()

        if Symbol.type in self:
            written_type = self[Symbol.type].get_type()
            if written_type != expr_type:
                raise SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")

        scope.current_scope.add_binding(scope.VariableObject(var_name, mutable=False, var_type=expr_type))

        cpp_type = get_cpp_type(expr_type)
        return f'const {cpp_type} sn_{var_name} = {expr_code};\n'

class SetStatement(nodes.Node):
    def to_code(self):
        assign_op = self.get_scalar(Symbol.assignment_op)

        if Symbol.place_term in self:
            if self[Symbol.place_term][Symbol.base_expression][0].nodetype != Symbol.identifier:
                raise SereneTypeError(f"Invalid expression for left-hand side of 'set' statement at line number {scope.line_number}.")
            var_name = self[Symbol.place_term][Symbol.base_expression].get_scalar(Symbol.identifier)

            if assign_op != '=':
                lhs_code = self[Symbol.place_term].to_code(place_term_relative_set=True)     # adds read access for lhs
            else:
                lhs_code = self[Symbol.place_term].to_code()
            
            correct_type = self[Symbol.place_term].get_type()
        else:
            var_name = self.get_scalar(Symbol.identifier)
            lhs_code = 'sn_' + var_name

            scope.current_scope.add_access((var_name,), 'look')                        # adds read access for lhs

            correct_type = scope.current_scope.get_type_of(var_name)

        expr_code = self[Symbol.expression].to_code()
        expr_type = self[Symbol.expression].get_type()

        if expr_type != correct_type:
            raise SereneTypeError(f"Incorrect type for assignment to variable '{var_name}' at line number {scope.line_number}. Correct type is '{correct_type}'.")

        if assign_op != '=':
            if expr_type.base not in ('Int', 'Float'):
                raise SereneTypeError(f"Incorrect type for '{assign_op}' assignment operator at line number {scope.line_number}.")

        scope.current_scope.check_set(var_name)
        return f'{lhs_code} {assign_op} {expr_code};\n'

class PrintStatement(nodes.Node):
    def to_code(self):
        expr_code = [f"({x.to_code()})" for x in self]
        expr_code.append('std::endl;\n')
        return 'std::cout << ' + ' << '.join(expr_code)

class RunStatement(nodes.Node):
    def to_code(self):
        return self[Symbol.term].to_code() + ';\n'

class ReturnStatement(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        if type(self.data) == nodes.NodeMap:
            self.satisfies_return = True
        else:
            self.satisfies_return = False   # "return" without value
    
    def to_code(self):
        if type(self.data) == nodes.NodeMap:
            expr_code = self[Symbol.expression].to_code()
            if scope.current_func_type is None:
                raise SereneTypeError(f"Cannot return value from function with no return type at line number {scope.line_number}.")
            if self[Symbol.expression].get_type() != scope.current_func_type:
                raise SereneTypeError(f"Incorrect type for return statement at line number {scope.line_number}.")
            return f'return {expr_code};\n'
        else:
            if scope.current_func_type is not None:
                raise SereneTypeError(f"Return statement at line number {scope.line_number} has no value.")
            return 'return;\n'

class BreakStatement(nodes.Node):
    def to_code(self):
        if len(scope.loops) > 0:
            return 'break;\n'
        else:
            raise SereneScopeError(f"'break' cannot be used outside of a loop at line number {scope.line_number}.")

class ContinueStatement(nodes.Node):
    def to_code(self):
        if len(scope.loops) > 0:
            self.satisfies_return = scope.loops[-1].is_infinite
            return 'continue;\n'
        else:
            raise SereneScopeError(f"'continue' cannot be used outside of a loop at line number {scope.line_number}.")

class ExitStatement(nodes.Node):
    def to_code(self):
        self.satisfies_return = True
        return f"exit({self.get_scalar(Symbol.int_literal)});\n"

class ExpressionNode(nodes.Node):
    def get_type(self):
        if (self.count(Symbol.term) > 1):
            last_type = None
            accum_type = None
            for x in self:
                if last_type is None:
                    last_type = x.get_type()
                    accum_type = last_type
                if x.nodetype == Symbol.infix_op and type(x.data) != str and Symbol.comparison_op in x:
                    accum_type = typecheck.TypeObject('Bool')
                elif x.nodetype != Symbol.term:
                    continue
                else:
                    if x.get_type() != last_type:
                        raise SereneTypeError(f"Mismatching types for infix operator(s) at line number {scope.line_number}.")
            return accum_type
        else:
            return self[Symbol.term].get_type()
    
    def to_code(self, surrounding_accessor=None, enclosed=False):
        # "surrounding_accessor" should only be passed to top-level expression with an applied accessor
        # "enclosed" is used for if-statement conditions, where accesses need to be checked on an expression rather than a statement

        if enclosed:
            self.read_list = []     # Any variable that will be accessed with look or copy
            self.write_list = []    # Any variable that will be accessed with mutate or move
            self.delete_list = []   # Any variable that will be accessed with move
            # These lists contain tuples of (variable as ParameterObject or VariableObject, field_name1, field_name2, ...)
            scope.current_enclosure = self

        self.get_type()     # Just for error-checking
        code = ''
        last_term = None
        for i in range(len(self.data)):
            cur = self[i]
            if (cur.nodetype == Symbol.unary_op):
                if cur.data == 'not':
                    if self[i+1].get_type().base != 'Bool':
                        raise SereneTypeError(f"Incorrect type for boolean expression at line number {scope.line_number}.")
                code += cur.data + (' ' if cur.data != '-' else '')
            elif (cur.nodetype == Symbol.infix_op):
                if type(cur.data) != str:
                    if cur.get_scalar(0) in ('>', '<', '>=', '<='):
                        if self[i-1].get_type().base not in ('Int', 'Float', 'String', 'Char'):
                            raise SereneTypeError(f"Incorrect type for inequality expression at line number {scope.line_number}.")
                    code += ' ' + cur.get_scalar(0) + ' '
                else:
                    if cur.data in ('and', 'or'):
                        if self[i-1].get_type().base != 'Bool':
                           raise SereneTypeError(f"Incorrect type for boolean expression at line number {scope.line_number}.")
                    elif cur.data in ('+', '-', '*', '/', '%'):
                        if self[i-1].get_type().base not in ('Int', 'Float'):
                           raise SereneTypeError(f"Incorrect type for numeric expression at line number {scope.line_number}.")                 
                    code += ' ' + cur.data + ' '
            elif cur.nodetype == Symbol.term:
                last_term = cur
                if (self.count(Symbol.term) > 1) or (surrounding_accessor is None):
                    code += cur.to_code()
                else:
                    code += cur.to_code(surrounding_accessor=surrounding_accessor)
            else:
                raise TypeError
        
        self.is_temporary = (Symbol.infix_op in self) or (Symbol.unary_op in self) or (last_term.is_temporary)
        if not self.is_temporary and surrounding_accessor == 'move':
            code = f"std::move({code})"
        
        if enclosed:
            scope.current_scope.check_all_statement_accesses()

        return code

class TermNode(nodes.Node):
    def get_type_sequence(self):
        L: list[typecheck.TypeObject] = []
        base_type = self[0].get_type()
        L.append(base_type)

        if len(self.data) == 1:
            return L

        for i in range(1, len(self.data)):
            cur = self[i]
            prev_type = L[-1]

            if prev_type.base in typecheck.standard_types:
                prev_type_spec = typecheck.standard_types[prev_type.base]
            elif prev_type.base in typecheck.user_defined_types:
                prev_type_spec = typecheck.user_defined_types[prev_type.base]
            else:
                raise SereneTypeError(f"Unknown type in expression at line number {scope.line_number}.")
            
            if cur.nodetype == Symbol.field_access:
                L.append(cur.get_type(prev_type_spec))
            elif cur.nodetype == Symbol.method_call:
                L.append(cur.get_type(prev_type, prev_type_spec, is_last=(i + 1 == len(self.data))))
            elif cur.nodetype == Symbol.index_call:
                L.append(cur.get_type(prev_type))
            else:
                raise UnreachableError          
        return L
    
    def get_type(self):
        this_type = self.get_type_sequence()[-1]
        if this_type is None:
            raise SereneTypeError(f"Value of expression at line number {scope.line_number} is void.")
        else:
            return this_type
    
    def to_code(self, place_term_relative_set=False, surrounding_accessor=None):
        base_expr = self[0]
        inner_expr = base_expr[0]

        if len(self.data) > 1:
            type_seq = self.get_type_sequence()

        if inner_expr.nodetype == Symbol.identifier:
            self.is_temporary = False
            code = base_expr.to_code()      # This is a bit redundant, but it's done to check read access on the identifier
            self.var_tup = (inner_expr.data,)
        elif (inner_expr.nodetype == Symbol.expression):
            code = '(' + inner_expr.to_code() + ')'
            self.is_temporary = inner_expr.is_temporary
            if self.is_temporary:
                self.var_tup = None
            else:
                self.var_tup = inner_expr.var_tup
        else:
            code = base_expr.to_code()
            self.is_temporary = True
            self.var_tup = None

        extend_var_tup = True
        does_mutate = False
        for i in range(1, len(self.data)):
            current_type = type_seq[i-1]
            x = self[i]
            if x.nodetype == Symbol.field_access:
                code += x.to_code()
                if extend_var_tup and not self.is_temporary:
                    self.var_tup = self.var_tup + (x[Symbol.identifier],)
            else:
                extend_var_tup = False
                if x.nodetype == Symbol.index_call:
                    code += x.to_code()
                elif x.nodetype == Symbol.method_call:
                    if not self.is_temporary:
                        if Symbol.mutate_method_symbol in x:
                            does_mutate = True
                        # Method calls return temporary values, so only the first method call in a term needs to be scope-checked
                        self.is_temporary = True

                    code += x.to_code(current_type)
                else:
                    raise UnreachableError
        if place_term_relative_set:     # if this term is the left-hand side of something like 'set x[10] += 1', then 'x' must be added as a read access
            scope.current_scope.add_access(self.var_tup, 'look')
        else:  
            if self.is_temporary:
                if self.var_tup is not None:
                    accessor = 'mutate' if does_mutate else 'look'
                    scope.current_scope.add_access(self.var_tup, accessor)
            else:
                if surrounding_accessor is not None:
                    scope.current_scope.add_access(self.var_tup, surrounding_accessor)
        
        return code

class PlaceTermNode(TermNode):  # Identical to TermNode, except with no method calls (prevented in the parsing stage). Used for 'set' statements
    pass

class FieldAccessNode(nodes.Node):
    def get_type(self, prev_type_spec):
        field_name = self[Symbol.identifier].data
        if field_name in prev_type_spec.members:
            member_type = prev_type_spec.members[field_name]
            if member_type.params is not None and member_type.base not in ('Vector', 'Array'):
                raise UnreachableError
            return member_type
        else:
            raise SereneTypeError(f"Invalid field access in expression at line number {scope.line_number}.")

    def to_code(self):
        return '.sn_' + self.get_scalar(Symbol.identifier)

class MethodCallNode(nodes.Node):
    def get_type(self, prev_type, prev_type_spec, is_last = False):
        method_name = self[Symbol.identifier].data + ('!' if Symbol.mutate_method_symbol in self else '')
        if method_name in prev_type_spec.methods:
            method_return_type = prev_type_spec.methods[method_name][0]
            if method_return_type is None:
                if is_last:
                    return None
                else:
                    raise SereneTypeError(f"Method '{method_name}' in expression at line number {scope.line_number} has no return value.")
            elif isinstance(method_return_type, typecheck.TypeObject):
                return method_return_type
            elif isinstance(method_return_type, typecheck.TypeVar) and (prev_type.base == 'Vector') and (method_name == 'pop!'):
                return prev_type.params[0]
            else:
                printerr(type(method_return_type))
                raise UnreachableError
        else:
            raise SereneTypeError(f"Method '{method_name}' does not exist at line number {scope.line_number}.")
            
    def to_code(self, prev_type):
        code = ''
        if prev_type is None:
            raise UnreachableError
        
        method_name = self.get_scalar(Symbol.identifier)
        if prev_type.base in typecheck.standard_types:
            orig_type = typecheck.standard_types[prev_type.base]
        elif prev_type.base in typecheck.user_defined_types:
            orig_type = typecheck.user_defined_types[prev_type.base]
        else:
            raise UnreachableError
    
        if Symbol.mutate_method_symbol in self:
            full_method_name = method_name + '!'
        else:
            full_method_name = method_name
        if full_method_name not in orig_type.methods:
            raise SereneTypeError(f"Method '{method_name}' does not exist at line number {scope.line_number}.")

        code = '.sn_' + method_name + '('

        params = []
        orig_params = orig_type.methods[full_method_name][1]
        num_called_params = len(self[Symbol.function_call_parameters].data)

        if num_called_params > len(orig_params):
            raise SereneScopeError(f"Method '{method_name}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < len(orig_params):
            raise SereneScopeError(f"Function '{method_name}' is given too few parameters when called at line number {scope.line_number}.")

        for i in range(num_called_params):
            orig_param = orig_params[i]
            orig_accessor = orig_param.accessor
            
            orig_type = orig_param.var_type
            if isinstance(orig_type, typecheck.TypeVar):
                if prev_type.params is not None and prev_type.base in ('Vector', 'Array'):
                    orig_type = prev_type.params[0]
                else:
                    raise UnreachableError
            
            c_param = self[Symbol.function_call_parameters][i]
            
            params.append(c_param.to_code(original_accessor = orig_accessor, original_type = orig_type, function_name = method_name, param_name = orig_param.name, method=True))

        code += ', '.join(params) + ')'
        return code

class IndexCallNode(nodes.Node):
    def get_type(self, prev_type):
        if prev_type.base in ('Vector', 'Array'):
            if self[Symbol.expression].get_type().base != 'Int':
                raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
            return prev_type.params[0]
        elif prev_type.base == 'String':
            if self[Symbol.expression].get_type().base != 'Int':
                raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
            return typecheck.TypeObject('Char')
        else:
            raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
    
    def to_code(self):
        return '[' + self[Symbol.expression].to_code() + ']'

class BaseExpressionNode(nodes.Node):
    def get_type(self):
        if Symbol.literal in self:
            if Symbol.int_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Int')
            elif Symbol.float_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Float')
            elif Symbol.bool_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Bool')
            elif Symbol.string_literal in self[Symbol.literal]:
                return typecheck.TypeObject('String')
            elif Symbol.char_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Char')
            else:
                raise UnreachableError
        elif Symbol.expression in self:
            return self[Symbol.expression].get_type()
        elif Symbol.identifier in self:
            var_name = self.get_scalar(Symbol.identifier)
            if not scope.current_scope.check_read(var_name):
                raise SereneTypeError(f"Variable '{var_name}' is not defined at line number {scope.line_number}.")
            return scope.current_scope.get_type_of(var_name)
        elif Symbol.function_call in self:
            for y in scope.functions:
                if self[Symbol.function_call].get_scalar(Symbol.identifier) == y.get_scalar(Symbol.identifier):
                    break
            original_function = y
            if Symbol.type not in original_function:
                raise SereneTypeError(f"Function '{self[Symbol.function_call].get_scalar(Symbol.identifier)}' with no return value cannot be used as an expression at line number {scope.line_number}.")
            else:
                return original_function[Symbol.type].get_type()
        elif Symbol.constructor_call in self:
            return self[Symbol.constructor_call].get_type()
        else:
            raise UnreachableError
        
    def to_code(self):
        if Symbol.function_call in self:
            return self[Symbol.function_call].to_code()
        elif Symbol.constructor_call in self:
            return self[Symbol.constructor_call].to_code()
        elif Symbol.identifier in self:
            var_name = self.get_scalar(Symbol.identifier)
            if scope.current_scope.check_read(var_name):     # If the variable also needs to be mutated/moved, that will already be checked within TermNode or ExpressionNode
                return 'sn_' + var_name
            else:
                raise SereneScopeError(f"Variable '{var_name}' is not defined at line number {scope.line_number}.")
        elif Symbol.literal in self:
            if Symbol.bool_literal in self[Symbol.literal]:
                return self[Symbol.literal].get_scalar(0).lower()
            elif Symbol.string_literal in self[Symbol.literal]:
                return f"SN_String({self[Symbol.literal].get_scalar(0)})"
            else:
                return self[Symbol.literal].get_scalar(0)
        elif Symbol.expression in self:
            return '(' + self[Symbol.expression].to_code() + ')'

class FunctionCallNode(nodes.Node):
    def to_code(self):
        if self.get_scalar(Symbol.identifier) not in scope.function_names:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is not defined at line number {scope.line_number}.")
        code = 'sn_' + self.get_scalar(Symbol.identifier) + '('

        num_called_params = len(self[Symbol.function_call_parameters].data) if type(self[Symbol.function_call_parameters].data) == nodes.NodeMap else 0
        for y in scope.functions:
            if self.get_scalar(Symbol.identifier) == y.get_scalar(Symbol.identifier):
                break
        original_function = y

        if type(original_function[Symbol.function_parameters].data) != nodes.NodeMap:
            num_original_params = 0
        else:
            num_original_params = len(original_function[Symbol.function_parameters].data)
        if num_called_params > num_original_params:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < num_original_params:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is given too few parameters when called at line number {scope.line_number}.")

        params = []
        for i in range(num_called_params):
            o_param = original_function[Symbol.function_parameters][i]
            if Symbol.accessor in o_param:
                o_accessor = o_param.get_scalar(Symbol.accessor)
            else:
                o_accessor = 'look'
            
            o_type = original_function.my_scope.get_type_of(o_param.get_scalar(Symbol.identifier), persistent=True)
            
            c_param = self[Symbol.function_call_parameters][i]
            
            params.append(c_param.to_code(original_accessor = o_accessor, original_type = o_type, function_name = self.get_scalar(Symbol.identifier), param_name = o_param.get_scalar(Symbol.identifier)))

        code += ', '.join(params) + ')'
        return code

class ConstructorCallNode(nodes.Node):
    def get_type(self):
        type_name = self.get_scalar(Symbol.base_type)
        if type_name == 'Array':
            if len(self[Symbol.constructor_call_parameters].data) >= 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.expression:
                return typecheck.TypeObject(base='Array', params=[self[Symbol.constructor_call_parameters][0][0].get_type()])
            else:
                raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")        
        elif type_name == 'Vector':
            if len(self[Symbol.constructor_call_parameters].data) == 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.type:    # Vector(Int), Vector(String), etc.
                type_node = self[Symbol.constructor_call_parameters][0][0]
                return typecheck.TypeObject(base='Vector', params=[type_node.get_type()])
            elif len(self[Symbol.constructor_call_parameters].data) >= 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.expression:
                return typecheck.TypeObject(base='Vector', params=[self[Symbol.constructor_call_parameters][0][0].get_type()])
            else:
                raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
        elif type_name in typecheck.user_defined_types:
            return typecheck.TypeObject(base=type_name)
        else:
            raise SereneTypeError(f"Type constructor called at line number {scope.line_number} is not defined.")
    
    def to_code(self):
        type_name = self.get_scalar(Symbol.base_type)
        if type_name == 'Array':
            if len(self[Symbol.constructor_call_parameters].data) >= 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.expression:
                elems = []
                elem_type = None
                for i in range(len(self[Symbol.constructor_call_parameters].data)):
                    cur = self[Symbol.constructor_call_parameters][i][0]
                    if cur.nodetype != Symbol.expression:
                        raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                    elems.append(cur.to_code())
                    if elem_type is None:
                        elem_type = cur.get_type()
                    elif elem_type != cur.get_type():
                        raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                inner_code = '{' + ', '.join(elems) + '}'
                type_param = get_cpp_type(elem_type)
                return f"SN_Array<{type_param}>({inner_code})"
            else:
               raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.") 
        elif type_name == 'Vector':
            if len(self[Symbol.constructor_call_parameters].data) == 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.type:    # Vector(Int), Vector(String), etc.
                type_node = self[Symbol.constructor_call_parameters][0][0]
                type_param = get_cpp_type(type_node.get_type())
                return f"SN_Vector<{type_param}>()"
            elif len(self[Symbol.constructor_call_parameters].data) >= 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.expression:
                elems = []
                elem_type = None
                for i in range(len(self[Symbol.constructor_call_parameters].data)):
                    cur = self[Symbol.constructor_call_parameters][i][0]
                    if cur.nodetype != Symbol.expression:
                        raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                    elems.append(cur.to_code())
                    if elem_type is None:
                        elem_type = cur.get_type()
                    elif elem_type != cur.get_type():
                        raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                inner_code = '{' + ', '.join(elems) + '}'
                type_param = get_cpp_type(elem_type)
                return f"SN_Vector<{type_param}>({inner_code})"
            else:
                raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
        elif type_name in typecheck.user_defined_types:
            type_spec = typecheck.user_defined_types[type_name]
            fields = []
            field_type = None

            if len(self[Symbol.constructor_call_parameters].data) > len(type_spec.constructor_params):
                raise SereneTypeError(f"Constructor for type '{type_name}' is given too many parameters when called at line number {scope.line_number}.")
            if len(self[Symbol.constructor_call_parameters].data) < len(type_spec.constructor_params):
                raise SereneTypeError(f"Constructor for type '{type_name}' is given too few parameters when called at line number {scope.line_number}.")

            for i in range(len(self[Symbol.constructor_call_parameters].data)):
                cur = self[Symbol.constructor_call_parameters][i][0]
                if cur.nodetype != Symbol.expression:
                    raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                
                field_type = type_spec.members[type_spec.constructor_params[i]]
                if field_type != cur.get_type():
                    raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
                
                fields.append(cur.to_code())
            
            inner_code = '{' + ', '.join(fields) + '}'
            return f"SN_{type_name} {inner_code}"
        else:
            raise SereneTypeError(f"Type constructor called at line number {scope.line_number} is not defined.")
        

class FunctionCallParameterNode(nodes.Node):
    def to_code(self, original_accessor, original_type, function_name, param_name, method=False):
        if Symbol.accessor in self:
            my_accessor = self.get_scalar(Symbol.accessor)
        else:
            my_accessor = 'look'

        if original_type != self[Symbol.expression].get_type():
            if method:
                raise SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to method '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")
            else:
                raise SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to function '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")

        code = self[Symbol.expression].to_code(surrounding_accessor=my_accessor) # This will raise exceptions for incorrect accesses

        if (not self[Symbol.expression].is_temporary) and (my_accessor != original_accessor) and (my_accessor != 'copy'):
            if method:
                raise SereneScopeError(f"Method '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")
            else:
                raise SereneScopeError(f"Function '{function_name}' is called with incorrect accessor for parameter '{param_name}' at line number {scope.line_number}.")

        return code

class ForLoopNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)
        self.is_infinite = False

    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = scope.ScopeObject(scope.current_scope, loop=True)
        scope.loops.append(self)

        loopvar = self.get_scalar(Symbol.identifier)
        

        if self.count(Symbol.expression) == 2:   # start and endpoint
            var_type = self[1].get_type()
            if var_type != self[2].get_type():
                raise SereneTypeError(f"Mismatching types in for-loop at line number {scope.line_number}.")
            scope.current_scope.add_binding(scope.VariableObject(loopvar, mutable=False, var_type=var_type))

            startval = self[1].to_code()
            endval = self[2].to_code()

            statements = newindent.join([x.to_code() for x in self[Symbol.statements]])  # This must be run AFTER the previous two lines due to the side effects
            code = f'for (int sn_{loopvar} = {startval}; sn_{loopvar} < {endval}; sn_{loopvar}++) {{\n{newindent}{statements}{oldindent}}}\n'
        else:
            expr_type = self[Symbol.expression].get_type()
            if expr_type.base in ('Array', 'Vector'):
                var_type = expr_type.params[0]
                scope.current_scope.add_binding(scope.VariableObject(loopvar, mutable=False, var_type=var_type))
            else:
                raise SereneTypeError(f"Type '{expr_type.base}' is not iterable, at line number {scope.line_number}.")
            
            myrange = self[Symbol.expression].to_code()
            statements = newindent.join([x.to_code() for x in self[Symbol.statements]])  # This must be run AFTER the previous line due to the side effects
            cpp_type = get_cpp_type(var_type)
            code = f'for (const {cpp_type}& sn_{loopvar} : {myrange}) {{\n{newindent}{statements}{oldindent}}}\n'
        
        sub_indent()
        scope.current_scope = scope.current_scope.parent
        assert(scope.loops.pop() is self)

        return code

class WhileLoopNode(nodes.Node):
    def __init__(self, D):
        super().__init__(D)

        condition_is_true = False   # check for "while (True) ...", "while ((((True)))) ...", etc.
        cur = self[Symbol.expression]
        while cur.count(Symbol.term) == 1:
            if(len(cur[Symbol.term].data) == 1):
                term = cur[Symbol.term]
                base_expr = term[Symbol.base_expression]
                if base_expr[0].nodetype == Symbol.literal:
                    if base_expr[0][0].nodetype == Symbol.bool_literal and base_expr[0].get_scalar(Symbol.bool_literal) == "True":
                        condition_is_true = True
                        break
                elif base_expr[0].nodetype == Symbol.expression:
                    cur = base_expr[0]
                    continue
            break

        self.is_infinite = condition_is_true

    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = scope.ScopeObject(scope.current_scope, loop=True)
        scope.loops.append(self)

        condition = self[Symbol.expression].to_code(enclosed=True)

        statements, return_is_statisfied = StatementNode.process_statements(node=self[Symbol.statements], indent=newindent)
        code = f'while ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        sub_indent()
        self.satisfies_return = self.is_infinite and return_is_statisfied

        scope.current_scope = scope.current_scope.parent
        assert(scope.loops.pop() is self)

        return code

class IfBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = scope.ScopeObject(scope.current_scope)

        return_satisfaction_list = []
        bindings_to_delete = []

        code = ''
        cur = self[Symbol.if_branch]

        condition = cur[Symbol.expression].to_code(enclosed=True)

        statements, return_is_statisfied = StatementNode.process_statements(node=cur[Symbol.statements], indent=newindent, bindings_to_delete=bindings_to_delete)
        return_satisfaction_list.append(return_is_statisfied)

        if (cur[Symbol.expression].get_type().base != 'Bool'):
            raise SereneTypeError("Condition in if-statement must have type Bool.")

        code += f'if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

        scope.current_scope = scope.current_scope.parent

        if Symbol.else_branch in self:
            bound_elseif = len(self.data) - 1
        else:
            bound_elseif = len(self.data)
        
        for i in range(1, bound_elseif):
            scope.current_scope = scope.ScopeObject(scope.current_scope)

            cur = self[i]

            condition = cur[Symbol.expression].to_code(enclosed=True)

            statements, return_is_statisfied = StatementNode.process_statements(node=cur[Symbol.statements], indent=newindent, bindings_to_delete=bindings_to_delete)
            return_satisfaction_list.append(return_is_statisfied)

            if (cur[Symbol.expression].get_type().base != 'Bool'):
                raise SereneTypeError("Condition in if-statement must have type Bool.")

            code += f'{oldindent}else if ({condition}) {{\n{newindent}{statements}{oldindent}}}\n'

            scope.current_scope = scope.current_scope.parent
        
        if Symbol.else_branch in self:
            scope.current_scope = scope.ScopeObject(scope.current_scope)

            cur = self[Symbol.else_branch]
            statements, return_is_statisfied = StatementNode.process_statements(node=cur[Symbol.statements], indent=newindent, bindings_to_delete=bindings_to_delete)
            return_satisfaction_list.append(return_is_statisfied)

            code += f'{oldindent}else {{\n{newindent}{statements}{oldindent}}}\n'

            scope.current_scope = scope.current_scope.parent
        
        for s, name in bindings_to_delete:
            if name in s:   # Avoid deleting binding multiple times
                s.kill_binding(name)
        
        bindings_to_delete.clear()
        
        sub_indent()

        self.satisfies_return = all(return_satisfaction_list) and (Symbol.else_branch in self)

        return code

class MatchBlock(nodes.Node):
    def to_code(self):
        newindent, oldindent = add_indent()

        return_satisfaction_list = []
        has_else = False

        subject = self[Symbol.expression].to_code()
        subject_type = self[Symbol.expression].get_type()
        branches = []
        for x in self:
            if x.nodetype == Symbol.match_branch:
                scope.current_scope = scope.ScopeObject(scope.current_scope)
                
                if Symbol.expression in x:
                    conditions = []
                    for i in range(len(x.data) - 1):    # skip last element, which is 'statements'; all others are expressions
                        conditions.append('(' + x[i].to_code() + ' == ' + subject + ')')
                        expr_type = x[i].get_type()
                        if expr_type != subject_type:
                            raise SereneTypeError(f"Incorrect type in match statement at line number {scope.line_number}. Type must match subject of type '{subject_type}'.")
                    
                    conditions = ' or '.join(conditions)
                    if Symbol.statements in x:
                        statements, return_is_statisfied = StatementNode.process_statements(node=x[Symbol.statements], indent=newindent)
                    else:
                        statements = x[Symbol.statement].to_code()
                        return_is_statisfied = x[Symbol.statement].satisfies_return
                    branchcode = f'if ({conditions}) {{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                else:   # 'else' branch in 'match' block
                    has_else = True
                    if Symbol.statements in x:
                        statements, return_is_statisfied = StatementNode.process_statements(node=x[Symbol.statements], indent=newindent)
                    else:
                        statements = x[Symbol.statement].to_code()
                        return_is_statisfied = x[Symbol.statement].satisfies_return
                    branchcode = f'{{\n{newindent}{statements}{oldindent}}}\n'
                    branches.append(branchcode)
                
                return_satisfaction_list.append(return_is_statisfied)
                scope.current_scope = scope.current_scope.parent
        sub_indent()
        self.satisfies_return = all(return_satisfaction_list) and has_else
        return (f'{oldindent}else ').join(branches)

class StructDefinitionNode(nodes.Node):
    @staticmethod
    def topological_ordering():
        # Consider struct definitions as a directed graph
        G = dict()

        # We don't want the whole TypeSpecification object, just a list of adjacent nodes. (We also don't want to modify the TypeSpecification objects, which are used elsewhere.)
        for key, value in typecheck.user_defined_types.items():
            L = []
            for x in value.members.values():
                if x.base in typecheck.user_defined_types:
                    L.append(x.base)
                elif x.base in ('Vector', 'Array'):
                    y = x.params[0]
                    while True:
                        if y.base in typecheck.user_defined_types:
                            L.append(x.params[0].base)
                            break
                        elif y.base in ('Vector', 'Array'):
                            y = y.params[0]
                        elif y.params is None:
                            break
                        else:
                            raise UnreachableError
                elif x.params is None:
                    continue
                else:
                    raise UnreachableError
            G[key] = L
        
        S = G.copy()    # shallow copy (adjacency lists are aliased between S and G)

        # Find nodes with no incoming edges. (In other words, find structs that are not present as fields in any other structs.)
        for vertex, edges in G.items():
            for adjacent_vertex in edges:
                if adjacent_vertex == vertex:   # Represents a recursive type, which is not currently allowed
                    raise SereneTypeError(f"Struct '{vertex}' cannot have fields of its own type.")
                if adjacent_vertex in S:
                    S.pop(adjacent_vertex)
        # S should now contain nodes with no incoming edges

        # Perform Kahn's algorithm (as described here: https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm) to find
        # a topological ordering of graph nodes if one exists. Putting the struct definitions in this order, but reversed,
        # ensures that all structs in the generated C++ are defined before they are used.
        L = []      # This will contain the sorted elements

        while len(S) > 0:
            n = S.popitem()         # tuple of (vertex, edges)
            L.append(n)
            
            i = 0
            while len(n[1]) > 0:
                m = n[1].pop()     # remove edge from m to n from the graph (this affects G by aliasing)
                incoming_edges = False
                for vertex, edges in G.items():
                    for x in edges:
                        if x == m:
                            incoming_edges = True
                            break
                    else:
                        continue
                    break
                if not incoming_edges:
                    S[m] = G[m]
        
        for vertex, edges in G.items():
            if len(edges) > 0:
                # Graph has a cycle, and no topological ordering exists
                raise SereneTypeError("Cyclic struct definitions found, which cannot be constructed.")
        return [x[0] for x in L]

    def get_type_spec(self):
        self.my_scope = scope.ScopeObject(scope.top_scope)

        members = {}
        methods = {}
        constructor_params = []
        for i in range(1, len(self.data)):
            x = self[i]
            if x.nodetype == Symbol.extension:
                continue
            member_name = x.get_scalar(Symbol.identifier)
            if (member_name in members):
                raise SereneTypeError(f"Found multiple definitions for member '{member_name}' of struct '{self.get_scalar(Symbol.base_type)}'.")
            members[member_name] = x[Symbol.type].get_type()
            constructor_params.append(member_name)

            self.my_scope.add_persistent_binding(scope.VariableObject(name=member_name, mutable=True, var_type=members[member_name]))

        if Symbol.extension in self:
            if Symbol.definitions_extension in self[Symbol.extension]:
                method_definitions = self[Symbol.extension][Symbol.definitions_extension][Symbol.method_definitions]
                for x in method_definitions:
                    tup = x.to_tuple_description(self.my_scope)
                    bare_name = tup[0][0:-1] if tup[0][-1] == '!' else tup[0]
                    if bare_name in methods or bare_name in members:
                        raise SereneTypeError(f"Found multiple definitions for member '{member_name}' of struct '{self.get_scalar(Symbol.base_type)}'.")
                    else:
                        methods[tup[0]] = tup[1]
            else:
                raise UnreachableError
        return typecheck.TypeSpecification(members=members, methods=methods, constructor_params=constructor_params)
    
    def to_forward_declaration(self):
        struct_name = self.get_scalar(Symbol.base_type)
        return f"struct SN_{struct_name};"

    def to_code(self):
        struct_name = self.get_scalar(Symbol.base_type)
        cpp_fields = []
        visiting_params = [f"SN_{struct_name}"]
        for i in range(1, len(self.data)):
            x = self[i]
            if x.nodetype == Symbol.extension:
                continue
            member_name = x.get_scalar(Symbol.identifier)
            member_type = x[Symbol.type].get_type()
            visiting_params.append(f"sn_{member_name}")
            cpp_fields.append(f"    {get_cpp_type(member_type)} sn_{member_name}")
        inner_code = ';\n'.join(cpp_fields) + ';\n'

        inner_code += f"\n    friend std::ostream& operator<<(std::ostream& os, const SN_{struct_name}& obj) {{\n        print_struct(os, obj);\n        return os;\n    }}\n"

        if Symbol.extension in self and Symbol.definitions_extension in self[Symbol.extension]:
            method_definitions = self[Symbol.extension][Symbol.definitions_extension][Symbol.method_definitions]
            add_indent()
            inner_code += '\n' + '\n\n'.join([x.to_code() for x in method_definitions]) + '\n'
            sub_indent()

        visiting_code = ", ".join(visiting_params)
        code = f"struct SN_{struct_name} {{\n{inner_code}}};\n"
        code += f"VISITABLE_STRUCT({visiting_code});"
        return code
