import yaml
import sys
import argparse
import textwrap

from nodes import Node
import scope
import typecheck

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    lines = []
    for line in sys.stdin:
        lines.append(line)
    my_yaml = ''.join(lines)
    
    try:
        tree = yaml.safe_load(my_yaml)[0]
    except yaml.YAMLError as e:
        print(e)
        exit()

    scope.definitions = Node.create(tree)
    scope.functions = []
    struct_definitions = []
    for x in scope.definitions:
        if x.nodetype == 'function':
            if x['identifier'].data in scope.function_names:
                print("COMPILE ERROR:", f"Function '{x['identifier'].data}' has more than one definition.", sep="\n")
                exit(126)
            else:
                scope.functions.append(x)
                scope.function_names.append(x['identifier'].data)
        elif x.nodetype == 'struct_definition':
            struct_name = x.get_scalar('base_type')
            if (struct_name in typecheck.user_defined_types) or (struct_name in typecheck.standard_types):
                raise scope.SereneTypeError(f"Found duplicate type definition for type '{struct_name}'.")
            else:
                struct_definitions.append(x)
                typecheck.user_defined_types[struct_name] = x.get_type_spec()
        else:
            raise NotImplementedError(x.nodetype)

    if 'main' not in scope.function_names:
        print("COMPILE ERROR:", "No 'main()' function is defined.", sep="\n")
        exit(126)

    struct_forward_declarations = []
    struct_definition_code = []
    try:
        for x in struct_definitions:
            struct_forward_declarations.append(x.to_forward_declaration())
            struct_definition_code.append(x.to_code())
    except (scope.SereneScopeError, scope.SereneTypeError) as exc:
        print("COMPILE ERROR:", exc.message, sep="\n")
        exit(126)
    except Exception as exc:
        print(f"At struct definition for '{x.get_scalar('base_type')}':")
        raise exc

    function_code = []
    function_forward_declarations = []
    try:
        for x in scope.functions:
            function_forward_declarations.append(x.to_forward_declaration())
            function_code.append(x.to_code())
    except (scope.SereneScopeError, scope.SereneTypeError) as exc:
        print("COMPILE ERROR:", exc.message, sep="\n")
        exit(126)
    except Exception as exc:
        print(f"At source line number {scope.line_number}:")
        raise exc

    code = textwrap.dedent("""\
                           #include <iostream>
                           #include <cstdint>
                           #include "../lib/serene_array.hh"
                           #include "../lib/serene_string.hh"
                           #include "../lib/serene_vector.hh"
                           
                           """)
    #code += ('\n'.join(struct_forward_declarations)   + '\n\n') if len(struct_forward_declarations) > 0 else ''        #Not currently needed
    code += ('\n'.join(function_forward_declarations) + '\n\n') if len(function_forward_declarations) > 0 else ''
    code += ('\n\n'.join(struct_definition_code)      + '\n\n') if len(struct_definition_code) > 0 else ''
    code += ('\n\n'.join(function_code)               + '\n\n') if len(function_code) > 0 else ''
    code += 'int main() {\n    sn_main();\n    return 0;\n}\n'

    if args.output:
        with open(args.output, 'w') as file:
            file.write(code)
    else:
        print(code, end='')


if __name__ == '__main__':    
    main()