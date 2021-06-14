from __future__ import annotations
import scope

class TypeSpecification:
    def __init__(self, members: dict[str, str | TypeVar], methods: dict, typevar: TypeVar | None = None):
        self.members = members
        self.methods = methods
        self.typevar = typevar

class TypeObject:
    def __init__(self, base: str, params: list[TypeObject] | None = None):
        self.base = base
        self.params = params
    
    def __eq__(self, other):
        if isinstance(other, TypeObject):
            return (self.base == other.base) and (self.params == other.params)
        else:
            raise TypeError

class TypeVar:
    pass

vector_type_var = TypeVar()
array_type_var = TypeVar()
standard_types = {'Vector': TypeSpecification(members={"length": "Int"},
                                              methods={"append!": ("", [scope.ParameterObject('item', 'look', vector_type_var)]),
                                                       "delete!": ("", [scope.ParameterObject('index', 'look', 'Int')]),
                                                       "pop!":    (vector_type_var, [])
                                                      },
                                              typevar=vector_type_var),
                  'Array':  TypeSpecification(members={"length": "Int"}, methods={}, typevar=array_type_var),
                  'String': TypeSpecification(members={"length": "Int"},
                                              methods={"append!": ("", [scope.ParameterObject('item', 'look', 'Char')]),    #should "append!" take a Char or a string?
                                                       "delete!": ("", [scope.ParameterObject('index', 'look', 'Int')]),
                                                       "pop!":    ("Char", [])
                                                      },
                                              typevar=vector_type_var)}
