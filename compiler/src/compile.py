import yaml
import textwrap
import sys
from pathlib import Path
import subprocess

from src.common import *
from src.nodes import Node, StructDefinitionNode
from src import scope, typecheck


def parse_additional(filename, include_path):
    # Directory of /serene/compiler/
    compiler_dir = Path(__file__).parent.resolve().parent

    # Run Raku-based parser
    source_path = (include_path / Path(filename)).resolve()
    if source_path.is_file():
        completed_process = subprocess.run(['raku', 'src/parser.raku', source_path], cwd=compiler_dir, capture_output=True, text=True)
        printerr(completed_process.stderr, end='')
    else:
        printerr("Included file", filename, "does not exist.")
        exit(1)

    if completed_process.returncode == 0:
        return completed_process.stdout
    else:
        exit(1)

def main(my_yaml, include_path):
    try:
        tree = yaml.safe_load(my_yaml)[0]
    except yaml.YAMLError as e:
        printerr(e)
        exit(1)
    
    # Parse include statements and add to tree
    i = 0
    while i < len(tree['definitions']):
        x = tree['definitions'][i]
        if list(x.keys())[0] != 'include_statement':
            i += 1
            continue
        included_yaml = parse_additional(x['include_statement'][0]['file_name'], include_path)
        try:
            included_tree = yaml.safe_load(included_yaml)[0]
        except yaml.YAMLError as e:
            printerr(e)
            exit(1)
        
        tree['definitions'].pop(i)
        tree['definitions'].extend(included_tree['definitions'])

    scope.definitions = Node.create(tree)
    scope.functions = []
    struct_definitions = []
    for x in scope.definitions:
        if x.nodetype == Symbol.function:
            if x[Symbol.identifier].data in scope.function_names:
                printerr("COMPILE ERROR:", f"Function '{x[Symbol.identifier].data}' has more than one definition.", sep="\n")
                exit(1)
            else:
                scope.functions.append(x)
                scope.function_names.append(x[Symbol.identifier].data)
        elif x.nodetype == Symbol.struct_definition:
            struct_name = x.get_scalar(Symbol.base_type)
            if (struct_name in typecheck.user_defined_types) or (struct_name in typecheck.standard_types):
                raise SereneTypeError(f"Found duplicate type definition for type '{struct_name}'.")
            else:
                struct_definitions.append(x)
        else:
            raise NotImplementedError(x.nodetype)
    
    try:
        for x in struct_definitions:
            struct_name = x.get_scalar(Symbol.base_type)
            typecheck.user_defined_types[struct_name] = x.get_type_spec()
        for x in struct_definitions:
            struct_name = x.get_scalar(Symbol.base_type)
            x.process_methods(typespec=typecheck.user_defined_types[struct_name])
    except (SereneScopeError, SereneTypeError) as exc:
        printerr("COMPILE ERROR:", exc.message, sep="\n")
        exit(1)
    except Exception as exc:
        printerr(f"At struct definition for '{x.get_scalar(Symbol.base_type)}':")
        raise exc

    try:
        sorted_structs = StructDefinitionNode.topological_ordering()
    except (SereneTypeError) as exc:
        printerr("COMPILE ERROR:", exc.message, sep="\n")
        exit(1)
    
    struct_definitions.sort(key=lambda x: sorted_structs.index(x.get_scalar(Symbol.base_type)), reverse=True)


    if 'main' not in scope.function_names:
        printerr("COMPILE ERROR:", "No 'main()' function is defined.", sep="\n")
        exit(1)

    function_code = []
    function_forward_declarations = []
    try:
        for x in scope.functions:
            x.setup()
            if not x.generic:
                function_forward_declarations.append(x.to_forward_declaration())

        for x in scope.functions:
            if not x.generic:
                function_code.append(x.to_code())

        for x in scope.remaining_generic_functions:
            original_function, generic_combos_params_temp, generic_combos_type_params_temp = x

            original_function.my_scope.generic_combos_params_temp = generic_combos_params_temp
            original_function.my_scope.generic_combos_type_params_temp = generic_combos_type_params_temp
            scope.current_type_params = generic_combos_type_params_temp

            function_forward_declarations.append(original_function.to_forward_declaration())

            original_function.my_scope.generic_combos_params_temp = None
            original_function.my_scope.generic_combos_type_params_temp = None
            scope.current_type_params = None
        
        for x in scope.remaining_generic_functions:
            original_function, generic_combos_params_temp, generic_combos_type_params_temp = x

            original_function.reset_scope()

            original_function.my_scope.generic_combos_params_temp = generic_combos_params_temp
            original_function.my_scope.generic_combos_type_params_temp = generic_combos_type_params_temp
            scope.current_type_params = generic_combos_type_params_temp

            function_code.append(original_function.to_code())

            original_function.my_scope.generic_combos_params_temp = None
            original_function.my_scope.generic_combos_type_params_temp = None
            scope.current_type_params = None

    except (SereneScopeError, SereneTypeError) as exc:
        printerr("COMPILE ERROR:", exc.message, sep="\n")
        exit(1)
    except Exception as exc:
        printerr(f"At source line number {scope.line_number}:")
        raise exc

    # struct_forward_declarations = []    # Not currently needed
    struct_definition_code = []

    try:
        for x in struct_definitions:
            #struct_forward_declarations.append(x.to_forward_declaration())     # Not currently needed
            struct_definition_code.append(x.to_code())
    except (SereneScopeError, SereneTypeError) as exc:
        printerr("COMPILE ERROR:", exc.message, sep="\n")
        exit(1)
    except Exception as exc:
        printerr(f"At struct definition for '{x.get_scalar(Symbol.base_type)}':")
        raise exc

    code = textwrap.dedent("""\
                           #include <iostream>
                           #include <cstdint>
                           #include "../src/lib/serene_printing.hh"
                           #include "../src/lib/serene_array.hh"
                           #include "../src/lib/serene_string.hh"
                           #include "../src/lib/serene_vector.hh"
                           #include "../src/lib/serene_file.hh"
                           #include "../src/lib/serene_locale.hh"
                           
                           """)
    #code += ('\n'.join(struct_forward_declarations)   + '\n\n') if len(struct_forward_declarations) > 0 else ''        #Not currently needed
    code += ('\n\n'.join(struct_definition_code)      + '\n\n') if len(struct_definition_code) > 0 else ''
    code += ('\n'.join(function_forward_declarations) + '\n\n') if len(function_forward_declarations) > 0 else ''
    code += ('\n\n'.join(function_code)               + '\n\n') if len(function_code) > 0 else ''
    code += "int main() {\n    "
    code += "std::cout.imbue(std::locale(std::locale(), new SereneLocale));\n    "  # std::locale is implicitly reference-counted, so "new" is not an issue
    code += "std::cout.setf(std::ios::boolalpha);\n    "
    code += "sn_main();\n    "
    code += "return 0;\n}\n"

    return code
