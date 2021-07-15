from __future__ import annotations
import sys

def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

line_number = 1

class SereneScopeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SereneTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class VariableObject:
    def __init__(self, name, mutable, var_type):
        self.name = name
        self.mutable = mutable
        self.var_type = var_type
        assert type(self.var_type) != str

class ParameterObject:
    def __init__(self, name, accessor, var_type):
        self.name = name
        self.accessor = accessor
        self.var_type = var_type
        assert type(self.var_type) != str

class ScopeObject:
    def __init__(self, parent, loop = False):
        self.bindings = dict()
        
        # This is used for function signatures. When a parameter goes out of scope in the function body, it is
        # removed from bindings but not from persistent_bindings, so that other functions can still check the signature.
        self.persistent_bindings = dict()

        self.subscopes = []
        self.parent = parent
        self.loop = loop or (self.parent.loop if self.parent is not None else False)
        if self.parent is not None:
            self.parent.subscopes.append(self)

    def __contains__(self, key):
        return (key in self.bindings)
    
    def __getitem__(self, key):
        return self.bindings[key]

    def add_binding(self, binding_object):
        if binding_object.name in self:
            raise SereneScopeError(f"Variable '{binding_object.name}' defined at line {line_number} already exists in this scope.")
        self.bindings[binding_object.name] = binding_object

    def add_persistent_binding(self, binding_object):
        if binding_object.name in self:
            raise SereneScopeError(f"Variable '{binding_object.name}' defined at line {line_number} already exists in this scope.")
        self.persistent_bindings[binding_object.name] = binding_object
        self.bindings[binding_object.name] = binding_object
    
    def kill_binding(self, name):
        if name in self:
            if current_scope.loop:
                raise SereneScopeError(f"Variable '{name}' is moved or destroyed at line {line_number} in a loop where it may be accessed again.")
            del self.bindings[name]
        else:
            raise ValueError
    
    def get_type_of(self, name, persistent=False):
        if persistent:
            if (name in self.persistent_bindings):
                return self.persistent_bindings[name].var_type
            # No need to check parent, as function definitions cannot be nested
            else:
                raise ValueError
        else:
            if (name in self):
                return self[name].var_type
            elif self.parent is not None:
                return self.parent.get_type_of(name)
            else:
                raise ValueError

    def check_read(self, name):
        if (name in self):
            return True
        elif self.parent is not None:
            return self.parent.check_read(name)
        else:
            return False
    
    def check_set(self, name):
        cur = self
        while cur != top_scope:
            if (name in cur):
                if type(cur[name]) == VariableObject:
                    if not cur[name].mutable:
                        raise SereneScopeError(f"Cannot mutate a const identifier, at line number {line_number}.")
                    return
                elif type(cur[name]) == ParameterObject:
                    if cur[name].accessor == 'look':
                        raise SereneScopeError(f"Cannot mutate a 'look' parameter, at line number {line_number}.")
                    return
            else:
                cur = cur.parent
        raise SereneScopeError(f"Variable {name} is not defined at line number {line_number}.")

    def add_access(self, var_tup, accessor):    # var_tup is (var_name, field_name1, field_name2, ...)
        var_name = var_tup[0]
        cur = self
        while cur != top_scope:
            if (var_name in cur):
                binding_object = cur[var_name]
                break
            cur = cur.parent
        else:
            raise SereneScopeError(f"Variable {var_name} is not defined at line number {line_number}.")

        output = (binding_object,) + tuple(x for x in var_tup[1:])
        
        if accessor == 'mutate':
            current_statement.write_list.append(output)
        elif accessor == 'move':
            current_statement.write_list.append(output)
            current_statement.delete_list.append(output)
        else:
            current_statement.read_list.append(output)

    def check_all_statement_accesses(self):
        def conflict(A: tuple, B: tuple):
            min_len = min(len(A), len(B))
            return A[:min_len] == B[:min_len]

        # printerr("Line:", line_number)
        # printerr("READ:", current_statement.read_list)
        # printerr("WRITE:", current_statement.write_list)
        # printerr("DELETE:", current_statement.delete_list)
        # printerr()

        for x in current_statement.write_list:
            if type(x[0]) == VariableObject:
                if not x[0].mutable:
                    raise SereneScopeError(f"Cannot mutate a const identifier, at line number {line_number}.")
            elif type(x[0]) == ParameterObject:
                if x[0].accessor == 'look':
                    raise SereneScopeError(f"Cannot mutate a 'look' parameter, at line number {line_number}.")
            else:
                raise ValueError
            
            for y in current_statement.read_list:
                if conflict(x, y):
                    min_len = min(len(x), len(y))
                    if min_len > 1:
                        conflicting_path = x[0].name + '.' + '.'.join(x[1:min_len])
                    else:
                        conflicting_path = x[0].name
                    raise SereneScopeError(f"Cannot mutate '{conflicting_path}' that is also read in the same statement, at line number {line_number}.")
        
        while len(current_statement.write_list) > 0:
            x = current_statement.write_list.pop()
            for y in current_statement.write_list:
                if conflict(x, y):
                    min_len = min(len(x), len(y))
                    if min_len > 1:
                        conflicting_path = x[0].name + '.' + '.'.join(x[1:min_len])
                    else:
                        conflicting_path = x[0].name
                    raise SereneScopeError(f"Cannot mutate '{conflicting_path}' multiple times in single statement, at line number {line_number}.")
        
        for x in current_statement.delete_list:
            if len(x) > 1:
                raise SereneScopeError(f"Struct fields cannot be moved, at line number {line_number}.")
            
            if type(x[0]) == VariableObject:
                if not x[0].mutable:
                    raise SereneScopeError(f"Cannot move a const identifier, at line number {line_number}.")
            elif type(x[0]) == ParameterObject:
                if x[0].accessor == 'look':
                    raise SereneScopeError(f"Cannot move a 'look' parameter, at line number {line_number}.")
                if x[0].accessor == 'mutate':
                    raise SereneScopeError(f"Cannot move a 'mutate' parameter, at line number {line_number}.")               
            else:
                raise ValueError
            
            cur = self
            while cur != top_scope:
                if x[0].name in cur:
                    cur.kill_binding(x[0].name)
                    break
                cur = cur.parent
            else:
                raise SereneScopeError(f"Variable {x[0].name} is not defined at line number {line_number}.")

    # def check_return(self, name):   # Not currently used?
    #     if (name in self):
    #         binding_object = self[name]
    #         if type(binding_object) == VariableObject:
    #             return True
    #         elif type(binding_object) == ParameterObject:
    #             # How to handle returning look parameters? It should be allowed at some point, but probably with an explicit 'return copy x'
    #             return (binding_object.accessor == 'move') or (binding_object.accessor == 'copy')
    #         else:
    #             raise TypeError
    #     elif self.parent is not None:
    #         return self.parent.check_return(name)
    #     else:
    #         return False


top_scope = ScopeObject(None)
current_scope = top_scope
scope_for_setup = None
current_statement = None
current_func_name = None
current_func_type = None
loops: list = []
functions = None
function_names: list[str] = []
definitions = None
