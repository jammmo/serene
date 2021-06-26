import yaml
import sys
import argparse
import textwrap

from nodes import Node
import scope

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
    for x in scope.definitions:
        if x.nodetype == 'function':
            if x['identifier'].data in scope.function_names:
                print("COMPILE ERROR:", f"Function '{x['identifier'].data}' has more than one definition.", sep="\n")
                exit(126)
            else:
                scope.functions.append(x)
                scope.function_names.append(x['identifier'].data)
        elif x.nodetype == 'struct_definition':
            raise NotImplementedError(x.nodetype)
        else:
            raise NotImplementedError(x.nodetype)

    if 'main' not in scope.function_names:
        print("COMPILE ERROR:", "No 'main()' function is defined.", sep="\n")
        exit(126)

    function_code = []
    try:
        for x in scope.functions:
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
    code += '\n\n'.join(function_code)
    code += '\n\nint main() {\n    sn_main();\n    return 0;\n}\n'

    if args.output:
        with open(args.output, 'w') as file:
            file.write(code)
    else:
        print(code)


if __name__ == '__main__':    
    main()