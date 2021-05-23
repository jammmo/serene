import yaml
import sys

from node import Node

def main():
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
    for x in functions:
        function_code.append(x.to_code())
    code = '#include <iostream>\n#include <cstdint>\n#include <string>\n\n'
    code += '\n\n'.join(function_code)
    code += '\n\nint main() {\n    sn_main();\n    return 0;\n}\n'
    print(code)


if __name__ == '__main__':    
    main()