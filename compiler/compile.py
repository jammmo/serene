import yaml
import sys
import argparse

from node import Node
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

    functions = Node.create(tree)
    function_code = []
    try:
        for x in functions:
            function_code.append(x.to_code())
    except scope.SereneScopeError as exc:
        print("COMPILE ERROR:", exc.message, sep="\n")
        exit(126)

    code = '#include <iostream>\n#include <cstdint>\n#include <string>\n\n'
    code += '\n\n'.join(function_code)
    code += '\n\nint main() {\n    sn_main();\n    return 0;\n}\n'

    if args.output:
        with open(args.output, 'w') as file:
            file.write(code)
    else:
        print(code)


if __name__ == '__main__':    
    main()