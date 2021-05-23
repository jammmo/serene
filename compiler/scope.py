class VariableObject:
    def __init__(self, name, mutable):
        self.name = name
        self.mutable = mutable

class ParameterObject:
    def __init__(self, name, accessor):
        self.name = name
        self.accessor = accessor

class ScopeObject:
    def __init__(self, parent):
        self.bindings = dict()
        self.victim_bindings = dict()   # Bindings that have been moved/deleted and no longer exist
        self.subscopes = []
        self.parent = parent

    def __contains__(self, key):
        return (key in self.bindings)
    
    def __getitem__(self, key):
        return self.bindings[key]

    def add_binding(self, binding_object):
        if binding_object.name in self:
            raise ValueError
        self.bindings[binding_object.name] = binding_object
    
    def kill_binding(self, binding_object):
        if binding_object.name in self:
            self.victim_bindings[binding_object.name] = binding_object
            del self.bindings[binding_object.name]
    
    def check_read(self, name):
        if (name in self):
            return True
        elif self.parent is not None:
            return self.parent.check_read(name)
        else:
            return False

    def check_set(self, name):
        if (name in self):
            binding_object = self[name]
            if type(binding_object) == VariableObject:
                return binding_object.mutable
            elif type(binding_object) == ParameterObject:
                return (binding_object.accessor != 'look')
            else:
                raise TypeError
        elif self.parent is not None:
            return self.parent.check_set(name)
        else:
            return False
    
    def check_return(self, name):
        if (name in self):
            binding_object = self[name]
            if type(binding_object) == VariableObject:
                return True
            elif type(binding_object) == ParameterObject:
                # How to handle returning look parameters? It should be allowed at some point, but probably with an explicit 'return copy x'
                return (binding_object.accessor == 'move') or (binding_object.accessor == 'copy')
            else:
                raise TypeError
        elif self.parent is not None:
            return self.parent.check_return(name)
        else:
            return False

    def check_pass(self, name, param_accessor):
        if (name in self):
            if (param_accessor == 'look') or (param_accessor == 'copy'):
                return True
            else:
                binding_object = self[name]
                if type(binding_object) == VariableObject:
                    if (param_accessor == 'move'):
                        if binding_object.mutable:      # Can you move a 'const'? (Currently no, but should reconsider later...)
                            self.kill_binding(name)
                            return True
                        else:
                            return False
                    elif (param_accessor == 'mutate'):
                        return binding_object.mutable
                    else:
                        raise ValueError
                elif type(binding_object) == ParameterObject:
                    if (param_accessor == 'move'):
                        if (binding_object.accessor == 'move') or (binding_object.accessor == 'copy'):
                            self.kill_binding(name)
                            return True
                        else:
                            return False
                    elif (param_accessor == 'mutate'):
                        return (binding_object.accessor != 'look')
                    else:
                        raise ValueError
                else:
                    raise TypeError
        elif self.parent is not None:
            return self.parent.check_pass(name, param_accessor)
        else:
            return False
