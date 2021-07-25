from __future__ import annotations

from serene_common import *
from src import nodes

# Base Classes ________________________________________________________________

class NodeMap:
    def __init__(self, L: list[dict]):
        if type(L) != list:
            raise TypeError
        self.data = [Node.create(x) for x in L]
    
    def __getitem__(self, x: int | str):
        if isinstance(x, int):
            return self.data[x]
        if isinstance(x, str):
            for y in self.data:
                if y.nodetype == x:
                    return y
            raise IndexError
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
    @staticmethod
    def create(D: dict) -> Node:
        if type(D) == dict:
            assert(len(D) == 1)
            nodetype = list(D.keys())[0]
            mapping = {
                'function':                nodes.FunctionNode,
                'function_parameter':      nodes.FunctionParameterNode,
                'type':                    nodes.TypeNode,
                'statement':               nodes.StatementNode,
                'var_statement':           nodes.VarStatement,
                'const_statement':         nodes.ConstStatement,
                'set_statement':           nodes.SetStatement,
                'print_statement':         nodes.PrintStatement,
                'run_statement':           nodes.RunStatement,
                'return_statement':        nodes.ReturnStatement,
                'break_statement':         nodes.BreakStatement,
                'continue_statement':      nodes.ContinueStatement,
                'exit_statement':          nodes.ExitStatement,
                'expression':              nodes.ExpressionNode,
                'term':                    nodes.TermNode,
                'place_term':              nodes.PlaceTermNode,
                'base_expression':         nodes.BaseExpressionNode,
                'function_call':           nodes.FunctionCallNode,
                'method_call':             nodes.MethodCallNode,
                'constructor_call':        nodes.ConstructorCallNode,
                'index_call':              nodes.IndexCallNode,
                'field_access':            nodes.FieldAccessNode,
                'function_call_parameter': nodes.FunctionCallParameterNode,
                'for_loop':                nodes.ForLoopNode,
                'while_loop':              nodes.WhileLoopNode,
                'if_block':                nodes.IfBlock,
                'match_block':             nodes.MatchBlock,
                'struct_definition':       nodes.StructDefinitionNode,
            }
            if nodetype in mapping:
                return mapping[nodetype](D)
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
        
    def __getitem__(self, x) -> Node:
        if type(self.data) == NodeMap:
            y = self.data[x]
            if isinstance(y, Node):
                return y
        raise TypeError
    
    def get_scalar(self, x):
        y = self.data[x]
        if isinstance(y.data, str) or isinstance(y.data, int):
            return y.data
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
