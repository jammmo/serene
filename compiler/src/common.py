from __future__ import annotations
from typing import Type

import sys
import enum

def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class SereneScopeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SereneTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

@enum.unique
class Symbol(enum.Enum):
    line_number = enum.auto()       # Not an actual symbol, but it shows up in the parse tree
    separator = enum.auto()
    line_separator = enum.auto()
    end_separator = enum.auto()
    comment = enum.auto()
    line_comment = enum.auto()
    multiline_comment = enum.auto()
    definitions = enum.auto()
    statements = enum.auto()
    statement = enum.auto()
    literal = enum.auto()
    int_literal = enum.auto()
    float_literal = enum.auto()
    string_literal = enum.auto()
    char_literal = enum.auto()
    bool_literal = enum.auto()
    identifier = enum.auto()
    base_type = enum.auto()
    type = enum.auto()
    assignment_op = enum.auto()
    infix_op = enum.auto()
    comparison_op = enum.auto()
    unary_op = enum.auto()
    accessor = enum.auto()
    struct_member = enum.auto()
    struct_definition = enum.auto()
    include_statement = enum.auto()
    file_name = enum.auto()
    function = enum.auto()
    function_parameters = enum.auto()
    function_parameter = enum.auto()
    function_call = enum.auto()
    function_call_parameters = enum.auto()
    function_call_parameter = enum.auto()
    constructor_call = enum.auto()
    constructor_call_parameters = enum.auto()
    constructor_call_parameter = enum.auto()
    mutate_method_symbol = enum.auto()
    method_call = enum.auto()
    field_access = enum.auto()
    index_call = enum.auto()
    expression = enum.auto()
    base_expression = enum.auto()
    term = enum.auto()
    place_term = enum.auto()
    print_statement = enum.auto()
    var_statement = enum.auto()
    const_statement = enum.auto()
    set_statement = enum.auto()
    run_statement = enum.auto()
    return_statement = enum.auto()
    break_statement = enum.auto()
    continue_statement = enum.auto()
    exit_statement = enum.auto()
    while_loop = enum.auto()
    for_loop = enum.auto()
    if_block = enum.auto()
    if_branch = enum.auto()
    elseif_branch = enum.auto()
    else_branch = enum.auto()
    match_block = enum.auto()
    match_branch = enum.auto()
