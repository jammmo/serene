from __future__ import annotations
import scope

class TypeSpecification:
    def __init__(self, members: dict, methods: dict, typevar: TypeVar | None = None, constructor_params = None):
        self.members = members
        self.methods = methods
        self.typevar = typevar
        self.constructor_params = constructor_params

class TypeObject:
    def __init__(self, base: str, params: list[TypeObject] | None = None):
        self.base = base
        self.params = params
        assert type(self.base) == str
    
    def __eq__(self, other):
        if isinstance(other, TypeObject):
            return (self.base == other.base) and (self.params == other.params)
        else:
            raise TypeError
    
    def __str__(self):
        if self.params is None:
            return self.base
        else:
            return self.base + '{' + ', '.join([str(x) for x in self.params]) + '}'

class TypeVar:
    pass

vector_type_var = TypeVar()
array_type_var = TypeVar()
standard_types = {'Vector': TypeSpecification(members={},
                                              methods={"length":  ("Int", []),
                                                       "append!": ("", [scope.ParameterObject('item', 'look', vector_type_var)]),
                                                       "delete!": ("", [scope.ParameterObject('index', 'look', TypeObject('Int'))]),
                                                       "pop!":    (vector_type_var, [])
                                                      },
                                              typevar=vector_type_var),
                  'Array':  TypeSpecification(members={}, methods={"length":  ("Int", [])}, typevar=array_type_var),
                  'String': TypeSpecification(members={},
                                              methods={"length":  ("Int", []),
                                                       "append!": ("", [scope.ParameterObject('item', 'look', TypeObject('Char'))]),    #should "append!" take a Char or a string?
                                                       "delete!": ("", [scope.ParameterObject('index', 'look', TypeObject('Int'))]),
                                                       "pop!":    ("Char", [])
                                                      },
                                              typevar=vector_type_var)}

user_defined_types: dict = {}
