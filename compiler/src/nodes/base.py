from __future__ import annotations
from typing import Type, Iterator, Callable

from src.common import *
from src import nodes, typecheck

# Base Classes ________________________________________________________________

class NodeMap:
    def __init__(self, L: list[dict]):
        if type(L) != list:
            raise TypeError
        self.data = [Node.create(x) for x in L]
    
    def __getitem__(self, x: int | Symbol):
        if isinstance(x, int):
            return self.data[x]
        if isinstance(x, Symbol):
            for y in self.data:
                if y.nodetype == x:
                    return y
            raise IndexError
        raise TypeError
    
    def __contains__(self, x: int | Symbol):
        if isinstance(x, int):
            return x in self.data[x]
        if isinstance(x, Symbol):
            for y in self.data:
                if y.nodetype == x:
                    return True
            return False
        raise TypeError
    
    def count(self, x: Symbol):
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
            mapping = {
                Symbol.function:                nodes.FunctionNode,
                Symbol.method_definition:       nodes.MethodDefinitionNode,
                Symbol.function_parameter:      nodes.FunctionParameterNode,
                Symbol.type:                    nodes.TypeNode,
                Symbol.statement:               nodes.StatementNode,
                Symbol.var_statement:           nodes.VarStatement,
                Symbol.const_statement:         nodes.ConstStatement,
                Symbol.set_statement:           nodes.SetStatement,
                Symbol.print_statement:         nodes.PrintStatement,
                Symbol.run_statement:           nodes.RunStatement,
                Symbol.return_statement:        nodes.ReturnStatement,
                Symbol.break_statement:         nodes.BreakStatement,
                Symbol.continue_statement:      nodes.ContinueStatement,
                Symbol.exit_statement:          nodes.ExitStatement,
                Symbol.expression:              nodes.ExpressionNode,
                Symbol.term:                    nodes.TermNode,
                Symbol.place_term:              nodes.PlaceTermNode,
                Symbol.base_expression:         nodes.BaseExpressionNode,
                Symbol.function_call:           nodes.FunctionCallNode,
                Symbol.method_call:             nodes.MethodCallNode,
                Symbol.constructor_call:        nodes.ConstructorCallNode,
                Symbol.index_call:              nodes.IndexCallNode,
                Symbol.field_access:            nodes.FieldAccessNode,
                Symbol.function_call_parameter: nodes.FunctionCallParameterNode,
                Symbol.for_loop:                nodes.ForLoopNode,
                Symbol.while_loop:              nodes.WhileLoopNode,
                Symbol.if_block:                nodes.IfBlock,
                Symbol.match_block:             nodes.MatchBlock,
                Symbol.struct_definition:       nodes.StructDefinitionNode,
            }
            nodetypestr = list(D.keys())[0]
            nodetype = Symbol[nodetypestr]
            if nodetype in mapping:
                return mapping[nodetype](D)
            else:
                return Node(D)
        else:
            raise TypeError

    def __init__(self, D):
        self.nodetype = Symbol[list(D.keys())[0]]
        inside = D[self.nodetype.name]
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
    
    def count(self, x: Symbol):
        if (type(x) != Symbol) or (type(self.data) != NodeMap):
            raise TypeError
        return self.data.count(x)
    
    def __iter__(self) -> Iterator[Node]:
        if type(self.data) == NodeMap:
            return iter(self.data.data)
        else:
            return iter([])
    
    def __str__(self):
        raise TypeError

    def __repr__(self):
        if type(self.data) == NodeMap:
            return '<' + self.nodetype.name + '>\n  ' + '\n  '.join(repr(self.data).split('\n')) + '\n</' + self.nodetype.name + '>'
        else:
            return '<' + self.nodetype.name + ': ' + repr(self.data if self.data != '' else None) + '>'

    get_type: Callable[..., typecheck.TypeObject]
    to_code: Callable[..., str]