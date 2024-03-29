from __future__ import annotations
from typing import Type

from src.common import *
from src import typecheck, scope, nodes

# Constants ___________________________________________________________________

int_types = ['Int64', 'Int32', 'Int16', 'Int8', 'Uint64', 'Uint32', 'Uint16', 'Uint8']
float_types = ['Float64', 'Float32']

type_mapping = {'Int64':    'int64_t',
                'Int32':    'int32_t',
                'Int16':    'int16_t',
                'Int8':     'int8_t',
                'Uint64':   'uint64_t',
                'Uint32':   'uint32_t',
                'Uint16':   'uint16_t',
                'Uint8':    'uint8_t',
                'Bool':     'bool',
                'String':   'SN_String',
                'Float64':  'double',
                'Float32':  'float',
                'Char':     'char',
                'Vector':   'SN_Vector',
                'Array':    'SN_Array',
                'File':     'SN_File',
               }


# Global Variables ____________________________________________________________

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
    if base in type_mapping:
        cpp_type = type_mapping[base]
        if my_type.params is None:
            return cpp_type
        else:  # Generic type
            return cpp_type + '<' + get_cpp_type(my_type.params[0]) + '>'
    elif base in typecheck.user_defined_types:
        return f"SN_{base}"
    else:
        raise SereneTypeError(f"Unknown type: {my_type}.")

def check_basetype(base):
    assert type(base) == str
    return (base in type_mapping) or (base in typecheck.user_defined_types)

def check_solidified(my_type):
    assert type(my_type) == TypeNode
    if check_basetype(my_type.get_scalar(Symbol.base_type)):
        if Symbol.type_parameters in my_type:
            return all([check_solidified(x) for x in my_type[Symbol.type_parameters]])
        else:
            return True
    else:
        return False

def solidify_with_type_params(type_object):
    base = type_object.base
    if check_basetype(base):
        if type_object.params is not None:
            return typecheck.TypeObject(type_object.base, params=[solidify_with_type_params(x) for x in type_object.params])
        else:
            return typecheck.TypeObject(type_object.base)
    else:
        if base in scope.current_type_params:
            solidified_base = scope.current_type_params[base].base
            if type_object.params is not None:
                return typecheck.TypeObject(solidified_base, params=[solidify_with_type_params(x) for x in type_object.params])
            else:
                return typecheck.TypeObject(solidified_base)
        else:
            raise SereneTypeError(f"Unknown type: {base}.")

def cosolidify(type1, type2):
    base1 = type1.base
    base2 = type2.base
    if check_basetype(base1) and check_basetype(base2):
        if base1 != base2:
            return None

        if type1.params is None and type2.params is None:
            return typecheck.TypeObject(base1)
        elif type1.params is None or type2.params is None:
            return typecheck.TypeObject(base1, params=type1.params if type1.params is not None else type2.params)
        else:
            assert len(type1.params) == len(type2.params)
            return typecheck.TypeObject(base1, params=[cosolidify(x, y) for x, y in zip(type1.params, type2.params)])
    else:
        return None

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
    
    def setup(self):
        scope.scope_for_setup = self.my_scope

        if Symbol.def_type_parameters in self:
            self.generic = True
            for x in self[Symbol.def_type_parameters]:
                name = x.data
                if check_basetype(name):
                    raise SereneTypeError(f"Type parameter name '{name}' in function '{self.get_scalar(Symbol.identifier)} collides with existing type name.")
                
                if name not in scope.scope_for_setup.type_parameters:
                    scope.scope_for_setup.type_parameters[name] = scope.TypeParameterObject(name)
                else:
                    # catches something like: function foo(x: T) on (type T, type T) {...}
                    raise SereneTypeError(f"Multiple definitions for type parameter '{name}' in function '{self.get_scalar(Symbol.identifier)}'.")
            
            for x in self[Symbol.function_parameters]:
                x.setup(generic=True)
        else:
            self.generic = False
            for x in self[Symbol.function_parameters]:
                base = x[Symbol.type].get_scalar(Symbol.base_type)
                if not check_basetype(base):
                    raise SereneTypeError(f"Unknown type: {base}.")
                x.setup()

    def reset_scope(self):
        # Since a generic function's statements are processed multiple times (once for each instance of the type parameters),
        # this function resets all the variables in self.my_scope so there are no duplicates
        scope.scope_for_setup = self.my_scope

        self.my_scope.bindings.clear()
        self.my_scope.persistent_bindings.clear()

        for x in self[Symbol.function_parameters]:
            x.setup(generic=True)

    def to_forward_declaration(self):
        if Symbol.type in self:
            if check_solidified(self[Symbol.type]):
                func_type = self[Symbol.type].to_code()  # C++ return type
            else:
                func_type = get_cpp_type(solidify_with_type_params(self[Symbol.type].get_type()))
        else:
            func_type = 'void'
        func_name = self.get_scalar(Symbol.identifier)

        if self.generic:
            func_parameters_list = []
            for i in range(len(self.my_scope.generic_combos_params_temp)):
                func_parameters_list.append(self[Symbol.function_parameters][i].to_code(my_type=self.my_scope.generic_combos_params_temp[i]))
            func_parameters = ', '.join(func_parameters_list)
        else:
            func_parameters = ', '.join([x.to_code() for x in self[Symbol.function_parameters]])

        code = f'{func_type} sn_{func_name}({func_parameters});'

        return code
    
    def to_code(self):
        newindent, oldindent = add_indent()

        scope.current_scope = self.my_scope

        if Symbol.type in self:
            if check_solidified(self[Symbol.type]):
                scope.current_func_type = self[Symbol.type].get_type()
            else:
                scope.current_func_type = solidify_with_type_params(self[Symbol.type].get_type())

            func_type = get_cpp_type(scope.current_func_type)  # C++ return type
            return_is_statisfied = False            
        else:
            func_type = 'void'
            return_is_statisfied = True     # No need to return a value anywhere            
        func_name = self.get_scalar(Symbol.identifier)
        
        if self.generic:
            func_parameters_list = []
            for i in range(len(self.my_scope.generic_combos_params_temp)):
                func_parameters_list.append(self[Symbol.function_parameters][i].to_code(my_type=self.my_scope.generic_combos_params_temp[i]))
            func_parameters = ', '.join(func_parameters_list)
        else:
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
        
        # return tuple similar to ("delete!", ("", [scope.ParameterObject('index', 'look', TypeObject('Int64'))]))

        parameter_list = []
        self.my_scope = scope.ScopeObject(parent=parent_scope, nonmut_method=(Symbol.mutate_method_symbol not in self))
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
    def setup(self, generic=False):
        var_name = self.get_scalar(Symbol.identifier)
        my_type = self[Symbol.type].get_type()
        if Symbol.accessor in self:
            accessor = self.get_scalar(Symbol.accessor)
        else:
            accessor = 'look'

        # Adds to the scope INSIDE the function, not the scope where the function is defined
        scope.scope_for_setup.add_persistent_binding(scope.ParameterObject(var_name, accessor, my_type, generic=generic))

        if generic:
            self.generic = True
        else:
            self.generic = False
            
            code = self[Symbol.type].to_code()

            if accessor == 'look':
                code += ' const&'
            elif accessor == 'mutate':
                code += '&'
            elif accessor == 'move':
                code += '&&'
            # When accessor is 'copy', the default pass-by-value behavior in C++ is correct, so no additional modifiers are needed

            code += ' ' + 'sn_'+ var_name

            self.code = code
    
    def to_code(self, my_type=None):
        if self.generic:
            assert my_type is not None

            var_name = self.get_scalar(Symbol.identifier)
            if Symbol.accessor in self:
                accessor = self.get_scalar(Symbol.accessor)
            else:
                accessor = 'look'

            code = get_cpp_type(my_type)

            if accessor == 'look':
                code += ' const&'
            elif accessor == 'mutate':
                code += '&'
            elif accessor == 'move':
                code += '&&'
            # When accessor is 'copy', the default pass-by-value behavior in C++ is correct, so no additional modifiers are needed

            code += ' ' + 'sn_'+ var_name
            return code
        else:
            return self.code

class TypeNode(nodes.Node):
    def get_type(self, allow_partial=False):
        base = self[Symbol.base_type].data
        num_generic_params = 0 if (Symbol.type_parameters not in self) else self[Symbol.type_parameters].count(Symbol.type)
        if num_generic_params == 0:
            return typecheck.TypeObject(base, allow_partial=allow_partial)
        elif num_generic_params == 1:
            if base not in ('Vector', 'Array'):
                if base in typecheck.user_defined_types:
                    raise SereneTypeError(f"Unnecessary type parameter specified for non-generic type '{base}'.")
                else:
                    raise SereneTypeError(f"Unknown generic type: {base}.")
            return typecheck.TypeObject(base, [self[Symbol.type_parameters][Symbol.type].get_type(allow_partial=allow_partial)])
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

        if Symbol.type in self:
            written_type = self[Symbol.type].get_type(allow_partial=True)
            expr_type = self[Symbol.expression].get_type(expected_type=written_type)    # expected_type is used only for disambiguating literals
            
            new_type = cosolidify(written_type, expr_type)
            if new_type is None:
                raise SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")
            expr_code = self[Symbol.expression].to_code(expected_type=new_type)
        else:
            expr_type = self[Symbol.expression].get_type()
            expr_code = self[Symbol.expression].to_code()

        scope.current_scope.add_binding(scope.VariableObject(var_name, mutable=True, var_type=expr_type))

        cpp_type = get_cpp_type(solidify_with_type_params(expr_type))

        return f'{cpp_type} sn_{var_name} = {expr_code};\n'

class ConstStatement(nodes.Node):
    def to_code(self):
        var_name = self.get_scalar(Symbol.identifier)

        if Symbol.type in self:
            written_type = self[Symbol.type].get_type(allow_partial=True)
            expr_type = self[Symbol.expression].get_type(expected_type=written_type)    # expected_type is used only for disambiguating literals
            
            new_type = cosolidify(written_type, expr_type)
            if new_type is None:
                raise SereneTypeError(f"Explicit type does not match expression type in declaration at line number {scope.line_number}.")
            expr_code = self[Symbol.expression].to_code(expected_type=new_type)
        else:
            expr_type = self[Symbol.expression].get_type()
            expr_code = self[Symbol.expression].to_code()

        scope.current_scope.add_binding(scope.VariableObject(var_name, mutable=False, var_type=expr_type))

        cpp_type = get_cpp_type(solidify_with_type_params(expr_type))

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
            if var_name == 'self':
                raise SereneScopeError(f"Invalid usage of 'self', at line number {scope.line_number}.")
            lhs_code = 'sn_' + var_name

            scope.current_scope.add_access((var_name,), 'look')                        # adds read access for lhs

            correct_type = scope.current_scope.get_type_of(var_name)

        expr_code = self[Symbol.expression].to_code(expected_type=correct_type)
        expr_type = self[Symbol.expression].get_type(expected_type=correct_type)

        if expr_type != correct_type:
            raise SereneTypeError(f"Incorrect type for assignment to variable '{var_name}' at line number {scope.line_number}. Correct type is '{correct_type}'.")

        if assign_op != '=':
            if expr_type.base not in (*int_types, *float_types):
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
            if solidify_with_type_params(self[Symbol.expression].get_type()) != scope.current_func_type:
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
    def get_type(self, expected_type=None):
        if (self.count(Symbol.term) > 1):
            last_type = None
            accum_type = None
            for x in self:
                if x.nodetype == Symbol.unary_op:
                    continue
                if last_type is None:
                    last_type = x.get_type()
                    accum_type = last_type
                if x.nodetype == Symbol.infix_op and type(x.data) != str and Symbol.comparison_op in x:
                    accum_type = typecheck.TypeObject('Bool')
                elif x.nodetype != Symbol.term:
                    continue
                else:
                    if scope.current_type_params is not None:
                        if solidify_with_type_params(x.get_type()) != solidify_with_type_params(last_type):
                            tp_str = '(' + ', '.join([f"type {x}: {y}" for x, y in scope.current_type_params.items()]) + ')'
                            raise SereneTypeError(f"Mismatching types for infix operator(s) in generic function with parameters {tp_str}, at line number {scope.line_number}.")
                    else:
                        if x.get_type() != last_type:
                            raise SereneTypeError(f"Mismatching types for infix operator(s) at line number {scope.line_number}.")
            return accum_type
        else:
            return self[Symbol.term].get_type(expected_type=expected_type)
    
    def to_code(self, surrounding_accessor=None, enclosed=False, expected_type=None, passthrough_negative=False):
        # "surrounding_accessor" should only be passed to top-level expression with an applied accessor
        # "enclosed" is used for if-statement conditions, where accesses need to be checked on an expression rather than a statement

        if enclosed:
            self.read_list = []     # Any variable that will be accessed with look or copy
            self.write_list = []    # Any variable that will be accessed with mutate or move
            self.delete_list = []   # Any variable that will be accessed with move
            # These lists contain tuples of (variable as ParameterObject or VariableObject, field_name1, field_name2, ...)
            scope.current_enclosure = self

        self.get_type(expected_type=expected_type)     # Just for error-checking
        code = ''
        last_term = None
        for i in range(len(self.data)):
            cur = self[i]
            if (cur.nodetype == Symbol.unary_op):
                if cur.data == 'not':
                    if solidify_with_type_params(self[i+1].get_type()).base != 'Bool':
                        if scope.current_type_params is not None:
                            tp_str = '(' + ', '.join([f"type {x}: {y}" for x, y in scope.current_type_params.items()]) + ')'
                            raise SereneTypeError(f"Incorrect type for boolean expression in generic function with parameters {tp_str}, at line number {scope.line_number}.")
                        else:
                            raise SereneTypeError(f"Incorrect type for boolean expression at line number {scope.line_number}.")
                if cur.data == '-' and expected_type is not None and len(self.data) == 2:
                    if passthrough_negative == True:
                        raise UnreachableError
                    passthrough_negative = True
                else:
                    code += cur.data + (' ' if cur.data != '-' else '')
            elif (cur.nodetype == Symbol.infix_op):
                if type(cur.data) != str:
                    if cur.get_scalar(0) in ('>', '<', '>=', '<='):
                        if solidify_with_type_params(self[i-1].get_type()).base not in (*int_types, *float_types, 'String', 'Char'):
                            if scope.current_type_params is not None:
                                tp_str = '(' + ', '.join([f"type {x}: {y}" for x, y in scope.current_type_params.items()]) + ')'
                                raise SereneTypeError(f"Incorrect type for inequality expression in generic function with parameters {tp_str}, at line number {scope.line_number}.")
                            else:
                                raise SereneTypeError(f"Incorrect type for inequality expression at line number {scope.line_number}.")
                    code += ' ' + cur.get_scalar(0) + ' '
                else:
                    if cur.data in ('and', 'or'):
                        if solidify_with_type_params(self[i-1].get_type()).base != 'Bool':
                            if scope.current_type_params is not None:
                                tp_str = '(' + ', '.join([f"type {x}: {y}" for x, y in scope.current_type_params.items()]) + ')'
                                raise SereneTypeError(f"Incorrect type for boolean expression in generic function with parameters {tp_str}, at line number {scope.line_number}.")
                            else:
                                raise SereneTypeError(f"Incorrect type for boolean expression at line number {scope.line_number}.")
                    elif cur.data in ('+', '-', '*', '/', '%'):
                        if solidify_with_type_params(self[i-1].get_type()).base not in (*int_types, *float_types):
                            if scope.current_type_params is not None:
                                tp_str = '(' + ', '.join([f"type {x}: {y}" for x, y in scope.current_type_params.items()]) + ')'
                                raise SereneTypeError(f"Incorrect type for numeric expression in generic function with parameters {tp_str}, at line number {scope.line_number}.")
                            else:
                                raise SereneTypeError(f"Incorrect type for numeric expression at line number {scope.line_number}.")
                    code += ' ' + cur.data + ' '
            elif cur.nodetype == Symbol.term:
                last_term = cur
                if (self.count(Symbol.term) > 1) or (surrounding_accessor is None):
                    if passthrough_negative:
                        code += cur.to_code(expected_type=expected_type, passthrough_negative=True)
                        passthrough_negative = False
                    else:
                        code += cur.to_code(expected_type=expected_type)
                else:
                    if passthrough_negative:
                        code += cur.to_code(surrounding_accessor=surrounding_accessor, expected_type=expected_type, passthrough_negative=True)
                        passthrough_negative = False
                    else:
                        code += cur.to_code(surrounding_accessor=surrounding_accessor, expected_type=expected_type)
            else:
                raise TypeError
        
        self.is_temporary = (Symbol.infix_op in self) or (Symbol.unary_op in self) or (last_term.is_temporary)
        if not self.is_temporary and surrounding_accessor == 'move':
            code = f"std::move({code})"
        
        if enclosed:
            scope.current_scope.check_all_statement_accesses()

        return code

class TermNode(nodes.Node):
    def get_type_sequence(self, expected_type=None, type_params=None):
        L: list[typecheck.TypeObject] = []
        base_type = self[0].get_type(expected_type=expected_type)
        if base_type.base not in type_mapping and base_type.base not in typecheck.user_defined_types:
            if type_params is not None and base_type.base in type_params:
                base_type = type_params[base_type.base]
            else:
                raise SereneTypeError(f"Unknown type in expression at line number {scope.line_number}.")
        
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
    
    def get_type(self, expected_type=None):
        this_type = self.get_type_sequence(expected_type=expected_type, type_params=scope.current_type_params)[-1]
        if this_type is None:
            raise SereneTypeError(f"Value of expression at line number {scope.line_number} is void.")
        else:
            return this_type
    
    def to_code(self, place_term_relative_set=False, surrounding_accessor=None, expected_type=None, passthrough_negative=False):
        base_expr = self[0]
        inner_expr = base_expr[0]

        if len(self.data) > 1:
            type_seq = self.get_type_sequence(scope.current_type_params)

        if inner_expr.nodetype == Symbol.identifier:
            self.is_temporary = False
            code = base_expr.to_code()      # This is a bit redundant, but it's done to check read access on the identifier

            if inner_expr.data == 'self':
                if len(self.data) <= 1 or self[1].nodetype != Symbol.method_call:
                    raise SereneScopeError(f"Invalid usage of 'self', at line number {scope.line_number}.")
                code = "(*this)"

            self.var_tup = (inner_expr.data,)
        elif (inner_expr.nodetype == Symbol.expression):
            code = '(' + inner_expr.to_code(passthrough_negative=(passthrough_negative and len(self.data) == 1)) + ')'
            self.is_temporary = inner_expr.is_temporary
            if self.is_temporary:
                self.var_tup = None
            else:
                # If an expression is not temporary, it should consist of exactly one term and no other operators
                if (inner_expr.count(Symbol.term) != 1) or (Symbol.unary_op in inner_expr):
                    raise UnreachableError
                self.var_tup = inner_expr[Symbol.term].var_tup
        else:
            code = base_expr.to_code(expected_type=expected_type, passthrough_negative=(passthrough_negative and len(self.data) == 1))
            self.is_temporary = True
            self.var_tup = None
        
        if (passthrough_negative and len(self.data) > 1):
            code = '-' + code

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
                    orig_type = solidify_with_type_params(prev_type).params[0]
                else:
                    raise UnreachableError
            
            c_param = self[Symbol.function_call_parameters][i]
            
            params.append(c_param.to_code(original_accessor = orig_accessor, original_type = orig_type, function_name = method_name, param_name = orig_param.name, method=True))

        code += ', '.join(params) + ')'
        return code

class IndexCallNode(nodes.Node):
    def get_type(self, prev_type):
        if prev_type.base in ('Vector', 'Array'):
            if self[Symbol.expression].get_type().base != 'Int64':
                raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
            return prev_type.params[0]
        elif prev_type.base == 'String':
            if self[Symbol.expression].get_type().base != 'Int64':
                raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
            return typecheck.TypeObject('Char')
        else:
            raise SereneTypeError(f"Invalid type for index at line number {scope.line_number}.")
    
    def to_code(self):
        return '[' + self[Symbol.expression].to_code() + ']'

class BaseExpressionNode(nodes.Node):
    def get_type(self, expected_type=None):
        if Symbol.literal in self:
            if Symbol.type_solidifier in self[Symbol.literal] or expected_type is not None:
                if expected_type is not None:
                    solidified_type = expected_type
                else:
                    solidified_type = self[Symbol.literal][Symbol.type_solidifier][Symbol.type].get_type(allow_partial=True)

                if Symbol.int_literal in self[Symbol.literal]:
                    if solidified_type.base not in int_types or solidified_type.params is not None:
                        raise SereneTypeError(f"Type solidifier is not valid for literal at line number {scope.line_number}.")
                    return solidified_type
                elif Symbol.float_literal in self[Symbol.literal]:
                    if solidified_type.base not in float_types or solidified_type.params is not None:
                        raise SereneTypeError(f"Type solidifier is not valid for literal at line number {scope.line_number}.")
                    return solidified_type
                elif Symbol.bool_literal in self[Symbol.literal] and solidified_type.base == 'Bool':
                    return typecheck.TypeObject('Bool')
                elif Symbol.string_literal in self[Symbol.literal] and solidified_type.base == 'String':
                    return typecheck.TypeObject('String')
                elif Symbol.char_literal in self[Symbol.literal] and solidified_type.base == 'Char':
                    return typecheck.TypeObject('Char')
                elif Symbol.collection_literal in self[Symbol.literal]:
                    if solidified_type.base in ('Array', 'Vector'):
                        L = []
                        for x in self[Symbol.literal][Symbol.collection_literal]:
                            if solidified_type.params is None:
                                new_type = x.get_type()
                            else:
                                new_type = x.get_type(expected_type=solidified_type.params[0])
                            L.append(new_type)
                            if new_type != L[0]:
                                raise SereneTypeError(f"Mismatching types in collection literal at line number {scope.line_number}.")
                        if len(L) == 0 and solidified_type.base == 'Array':
                            raise SereneTypeError(f"Zero-length arrays are not currently allowed, at line number {scope.line_number}.")
                        if solidified_type.params is None:
                            return typecheck.TypeObject(solidified_type.base, params=[L[0]])
                        else:
                            return solidified_type
                    else:
                        raise SereneTypeError(f"Incorrect base type for collection literal at line number {scope.line_number}.")
            # If an expected type or type solidifier is passed but is incompatible with the literal, the logic above should
            # "fall through" to the general cases below. The type returned will be based on just the literal, but the incompatibility
            # should throw an error elsewhere.
            
            if Symbol.int_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Int64')
            elif Symbol.float_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Float64')
            elif Symbol.bool_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Bool')
            elif Symbol.string_literal in self[Symbol.literal]:
                return typecheck.TypeObject('String')
            elif Symbol.char_literal in self[Symbol.literal]:
                return typecheck.TypeObject('Char')
            elif Symbol.collection_literal in self[Symbol.literal]:
                L = []
                for x in self[Symbol.literal][Symbol.collection_literal]:
                    new_type = x.get_type()
                    L.append(new_type)
                    if new_type != L[0]:
                        raise SereneTypeError(f"Mismatching types in collection literal at line number {scope.line_number}.")
                if len(L) == 0:
                    raise SereneTypeError(f"Unspeficied type for zero-length collection literal at line number {scope.line_number}.")
                return typecheck.TypeObject('Array', params=[L[0]])
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
                original_func_type = original_function[Symbol.type].get_type()

                if original_function.generic and original_func_type.base in original_function.my_scope.type_parameters:
                    self[Symbol.function_call].to_code(cache_types_only=True)    # Caches return type if it hasn't been computed yet
                    return self[Symbol.function_call].return_type
                return original_function[Symbol.type].get_type()
        elif Symbol.constructor_call in self:
            return self[Symbol.constructor_call].get_type()
        else:
            raise UnreachableError
        
    def to_code(self, expected_type=None, passthrough_negative=False):
        if Symbol.function_call in self:
            return ('-' if passthrough_negative else '') + self[Symbol.function_call].to_code()
        elif Symbol.constructor_call in self:
            return ('-' if passthrough_negative else '') + self[Symbol.constructor_call].to_code()
        elif Symbol.identifier in self:
            var_name = self.get_scalar(Symbol.identifier)
            if scope.current_scope.check_read(var_name):     # If the variable also needs to be mutated/moved, that will already be checked within TermNode or ExpressionNode
                return ('-' if passthrough_negative else '') + 'sn_' + var_name
            else:
                raise SereneScopeError(f"Variable '{var_name}' is not defined at line number {scope.line_number}.")
        elif Symbol.literal in self:
            if Symbol.bool_literal in self[Symbol.literal]:
                if passthrough_negative:
                    raise UnreachableError
                return self[Symbol.literal].get_scalar(0).lower()
            elif Symbol.string_literal in self[Symbol.literal]:
                if passthrough_negative:
                    raise UnreachableError
                return f"SN_String({self[Symbol.literal].get_scalar(0)})"
            elif Symbol.int_literal in self[Symbol.literal] or Symbol.float_literal in self[Symbol.literal]:
                if expected_type is not None:
                    return get_cpp_type(expected_type) + '{' + ('-' if passthrough_negative else '') + self[Symbol.literal].get_scalar(0) + '}'
                else:
                    return ('-' if passthrough_negative else '') + self[Symbol.literal].get_scalar(0)
            elif Symbol.collection_literal in self[Symbol.literal]:
                if expected_type is not None:
                    my_type = self.get_type(expected_type=expected_type)
                    code = get_cpp_type(my_type)
                else:
                    my_type = self.get_type()
                    code = get_cpp_type(self.get_type())

                if type(self[Symbol.literal][Symbol.collection_literal].data) == nodes.NodeMap:
                    return code + '({' + ', '.join([x.to_code(expected_type=my_type.params[0]) for x in self[Symbol.literal][Symbol.collection_literal]]) + '})'
                else:
                    return code + '()'
            else:
                if passthrough_negative:
                    raise UnreachableError
                return self[Symbol.literal].get_scalar(0)
        elif Symbol.expression in self:
            return '(' + self[Symbol.expression].to_code(passthrough_negative=passthrough_negative) + ')'
        else:
            raise UnreachableError

class FunctionCallNode(nodes.Node):
    def to_code(self, cache_types_only=False):
        if self.get_scalar(Symbol.identifier) not in scope.function_names:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is not defined at line number {scope.line_number}.")
        code = 'sn_' + self.get_scalar(Symbol.identifier) + '('

        num_called_params = len(self[Symbol.function_call_parameters].data) if type(self[Symbol.function_call_parameters].data) == nodes.NodeMap else 0
        original_function = None
        for y in scope.functions:
            if self.get_scalar(Symbol.identifier) == y.get_scalar(Symbol.identifier):
                original_function = y
                break
        if original_function is None:
            raise UnreachableError

        if type(original_function[Symbol.function_parameters].data) != nodes.NodeMap:
            num_original_params = 0
        else:
            num_original_params = len(original_function[Symbol.function_parameters].data)
        if num_called_params > num_original_params:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is given too many parameters when called at line number {scope.line_number}.")
        if num_called_params < num_original_params:
            raise SereneScopeError(f"Function '{self.get_scalar(Symbol.identifier)}' is given too few parameters when called at line number {scope.line_number}.")

        params_code = []
        reset_type_temp = False
        if original_function.generic:
            call_param_types = []
            for x in self[Symbol.function_call_parameters]:
                call_param_types.append(solidify_with_type_params(x[Symbol.expression].get_type()))
            
            already_exists = False
            for i in range(len(original_function.my_scope.generic_combos_params)):
                if call_param_types == original_function.my_scope.generic_combos_params[i]:
                    already_exists = True
                    reset_type_temp = True
                    for name, tparam in original_function.my_scope.type_parameters.items():
                        tparam.type_temp = original_function.my_scope.generic_combos_type_params[i][name]
                    break
            
            orig_param_types = [p[Symbol.type].get_type() for p in original_function[Symbol.function_parameters]]
            for i in range(len(orig_param_types)):
                orig_cur = orig_param_types[i]
                call_cur = call_param_types[i]
                while True:
                    if check_basetype(orig_cur.base) and orig_cur.params is None:
                        if orig_cur.base != call_cur.base:
                            raise SereneTypeError(f"Mismatching types in call to generic function at line number {scope.line_number}.")
                        break
                    elif check_basetype(orig_cur.base):
                        if len(orig_cur.params) > 1:
                            raise NotImplementedError
                        if orig_cur.base != call_cur.base:
                            raise SereneTypeError(f"Mismatching types in call to generic function at line number {scope.line_number}.")
                        orig_cur = orig_cur.params[0]
                        call_cur = call_cur.params[0]
                    else:
                        if orig_cur.params is not None:
                            raise NotImplementedError
                        if original_function.my_scope.type_parameters[orig_cur.base].type_temp is not None:
                            if original_function.my_scope.type_parameters[orig_cur.base].type_temp != call_cur:
                                raise UnreachableError
                        reset_type_temp = True
                        original_function.my_scope.type_parameters[orig_cur.base].type_temp = solidify_with_type_params(call_cur)
                        break

            generic_combos_params_temp = call_param_types
            generic_combos_type_params_temp = {k: v.type_temp for k, v in original_function.my_scope.type_parameters.items()}

            if reset_type_temp:
                for x in original_function.my_scope.type_parameters.values():
                    x.type_temp = None

            if not already_exists:
                original_function.my_scope.generic_combos_params.append(call_param_types)
                original_function.my_scope.generic_combos_type_params.append(generic_combos_type_params_temp)

            if Symbol.type in original_function:
                base = original_function[Symbol.type].get_scalar(Symbol.base_type)
                if check_basetype(base):
                    self.return_type = original_function[Symbol.type].get_type()
                else:
                    if base in original_function.my_scope.type_parameters:
                        if Symbol.type not in original_function[Symbol.type]:
                            self.return_type = generic_combos_type_params_temp[base]
                        else:
                            raise NotImplementedError   # Generic of a type parameter in return type?
                    else:
                        raise SereneTypeError(f"Unknown type: {base}.")

            if not already_exists:
                scope.remaining_generic_functions.append((original_function, generic_combos_params_temp, generic_combos_type_params_temp))

        if cache_types_only:
            return

        for i in range(num_called_params):
            o_param = original_function[Symbol.function_parameters][i]
            if Symbol.accessor in o_param:
                o_accessor = o_param.get_scalar(Symbol.accessor)
            else:
                o_accessor = 'look'
            
            c_param = self[Symbol.function_call_parameters][i]

            if original_function.generic:
                o_type = call_param_types[i]
            else:
                o_type = original_function.my_scope.get_type_of(o_param.get_scalar(Symbol.identifier), persistent=True)

            params_code.append(c_param.to_code(original_accessor = o_accessor,
                                original_type = o_type,
                                function_name = self.get_scalar(Symbol.identifier),
                                param_name = o_param.get_scalar(Symbol.identifier)))

        code += ', '.join(params_code) + ')'
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
            if len(self[Symbol.constructor_call_parameters].data) == 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.type:    # Vector(Int64), Vector(String), etc.
                type_node = self[Symbol.constructor_call_parameters][0][0]
                return typecheck.TypeObject(base='Vector', params=[type_node.get_type()])
            elif len(self[Symbol.constructor_call_parameters].data) >= 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.expression:
                return typecheck.TypeObject(base='Vector', params=[self[Symbol.constructor_call_parameters][0][0].get_type()])
            else:
                raise SereneTypeError(f"Invalid parameters for type constructor called at line number {scope.line_number}.")
        elif type_name == 'File':
            if len(self[Symbol.constructor_call_parameters].data) == 1:
                param = self[Symbol.constructor_call_parameters][0][0]
                if param.nodetype == Symbol.expression and param.get_type().base == 'String':
                    return typecheck.TypeObject(base='File')
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
            if len(self[Symbol.constructor_call_parameters].data) == 1 and self[Symbol.constructor_call_parameters][0][0].nodetype == Symbol.type:    # Vector(Int64), Vector(String), etc.
                type_node = self[Symbol.constructor_call_parameters][0][0]
                if check_solidified(type_node):
                    type_param = get_cpp_type(type_node.get_type())
                else:
                    type_param = get_cpp_type(solidify_with_type_params(type_node.get_type()))
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
        elif type_name == 'File':
            if len(self[Symbol.constructor_call_parameters].data) == 1:
                param = self[Symbol.constructor_call_parameters][0][0]
                if param.nodetype == Symbol.expression and param.get_type().base == 'String':
                    inner_code = param.to_code()
                    return f"SN_File({inner_code})"
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

        if solidify_with_type_params(original_type) != solidify_with_type_params(self[Symbol.expression].get_type(expected_type=original_type)):
            if method:
                raise SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to method '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")
            else:
                raise SereneTypeError(f"Incorrect type for parameter '{param_name}' of call to function '{function_name}' at line number {scope.line_number}. Correct type is '{original_type}'.")

        code = self[Symbol.expression].to_code(surrounding_accessor=my_accessor, expected_type=original_type) # This will raise exceptions for incorrect accesses

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
            elif expr_type.base == 'String':
                var_type = typecheck.TypeObject('Char')
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

            self.my_scope.add_persistent_binding(scope.VariableObject(name=member_name, mutable=True, var_type=members[member_name], is_field=True))

        self.my_scope.add_persistent_binding(scope.VariableObject(name='self', mutable=True, var_type=typecheck.TypeObject(self.get_scalar(Symbol.base_type)), is_self=True))

        # This typespec will have an empty dict of methods, which will be populated later by self.process_methods().
        # Basic struct definitions have to be processed before their method definitions because the methods may take
        # objects of any type (including the type being defined) as parameters.
        return typecheck.TypeSpecification(members=members, methods=methods, constructor_params=constructor_params)
    
    def process_methods(self, typespec):
        if Symbol.extension in self:
            members = typespec.members
            methods = typespec.methods

            if Symbol.definitions_extension in self[Symbol.extension]:
                method_definitions = self[Symbol.extension][Symbol.definitions_extension][Symbol.method_definitions]
                for x in method_definitions:
                    tup = x.to_tuple_description(self.my_scope)
                    bare_name = tup[0][0:-1] if tup[0][-1] == '!' else tup[0]
                    if bare_name in methods or bare_name in members:
                        raise SereneTypeError(f"Found multiple definitions for member '{bare_name}' of struct '{self.get_scalar(Symbol.base_type)}'.")
                    else:
                        methods[tup[0]] = tup[1]
            else:
                raise UnreachableError
    
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
