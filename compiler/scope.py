from __future__ import annotations

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
    
    def kill_binding(self, name):
        if name in self:
            if current_scope.loop:
                raise SereneScopeError(f"Variable '{name}' is moved or destroyed at line {line_number} in a loop where it may be accessed again.")
            del self.bindings[name]
        else:
            raise ValueError
    
    def get_type_of(self, name):
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

    # def check_set(self, name):
    #     if (name in self):
    #         binding_object = self[name]
    #         if type(binding_object) == VariableObject:
    #             return binding_object.mutable
    #         elif type(binding_object) == ParameterObject:
    #             return (binding_object.accessor != 'look')
    #         else:
    #             raise TypeError
    #     elif self.parent is not None:
    #         return self.parent.check_set(name)
    #     else:
    #         return False
    
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

    # def check_pass(self, name, param_accessor):
    #     if (name in self):
    #         if (param_accessor == 'look') or (param_accessor == 'copy'):
    #             return True
    #         else:
    #             binding_object = self[name]
    #             if type(binding_object) == VariableObject:
    #                 if (param_accessor == 'move'):
    #                     if binding_object.mutable:      # Can you move a 'const'? (Currently no, but should reconsider later...)
    #                         self.kill_binding(name)
    #                         return True
    #                     else:
    #                         return False
    #                 elif (param_accessor == 'mutate'):
    #                     if binding_object.mutable and binding_object not in current_statement.write_list:
    #                         current_statement.write_list.append(binding_object)
    #                         return True
    #                     else:
    #                         return False
    #                 else:
    #                     raise ValueError
    #             elif type(binding_object) == ParameterObject:
    #                 if (param_accessor == 'move'):
    #                     if (binding_object.accessor == 'move') or (binding_object.accessor == 'copy'):
    #                         self.kill_binding(name)
    #                         return True
    #                     else:
    #                         return False
    #                 elif (param_accessor == 'mutate'):
    #                     return (binding_object.accessor != 'look')
    #                 else:
    #                     raise ValueError
    #             else:
    #                 raise TypeError
    #     elif self.parent is not None:
    #         return self.parent.check_pass(name, param_accessor)
    #     else:
    #         return False
    
    def add_access(self, var_tup, accessor):    # var_tup is (var_name, field_name1, field_name2, ...)
        var_name = var_tup[0]
        cur = self
        while cur != top_scope:
            if (var_name in cur):
                binding_object = self[var_name]
                break
            cur = cur.parent
        else:
            raise SereneScopeError(f"Variable {var_name} is not defined at line number {line_number}.")

        output = tuple(x for x in var_tup)
        output[0] = binding_object

        current_statement.read_list.append(output)
        
        if accessor == 'mutate':
            current_statement.write_list.append(output)
        elif accessor == 'move':
            current_statement.write_list.append(output)
            current_statement.delete_list.append(output)

    def check_all_statement_accesses(self):
        def conflict(A: tuple, B: tuple):
            min_len = min(len(A), len(B))
            return A[:min_len] == B[:min_len]

        print("Line:", line_number)
        print(current_statement.read_list)
        print(current_statement.write_list)
        print(current_statement.delete_list)
        print()

        for x in current_statement.write_list:
            if type(x[0]) == VariableObject:
                assert x[0].mutable
            elif type(x[0]) == ParameterObject:
                assert x[0].accessor != 'look'
            else:
                raise ValueError
            
            for y in current_statement.read_list:
                assert not conflict(x, y)
        
        while len(current_statement.write_list) > 0:
            x = current_statement.write_list.pop()
            for y in current_statement.read_list:
                assert not conflict(x, y)
        
        for x in current_statement.delete_list:
            if len(x) > 1:
                raise SereneScopeError(f"Fields of structs cannot be moved, at line number {line_number}.")
            
            if type(x[0]) == VariableObject:
                assert x[0].mutable
            elif type(x[0]) == ParameterObject:
                assert x[0].accessor not in ('look', 'mutate')
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



top_scope = ScopeObject(None)
current_scope = top_scope
init_scope = None
current_statement = None
current_func_name = None
current_func_type = None
loops: list = []
functions = None
function_names: list[str] = []
definitions = None
