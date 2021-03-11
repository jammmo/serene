from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ['SereneLexer']

class SereneLexer(RegexLexer):
    name = 'Serene'
    aliases = ['serene']
    filenames = ['*.sn']

    tokens = {
        'root': [
            (r'\b(if|else|elseif|while|for|return|break|either|continue|match|is)\b', Keyword),
            (r'\b(set|var|const|bind|run|import|or|not|and|print|throw)\b', Keyword),
            (r'\b(function|method|specifics|signatures|friend|constructor|interface|type|subscript|with|implements|struct|enum|tuple)\b', Keyword),
            (r'\b(mut|mutate|move|copy|maybe|defined|undefined|True|False)\b', Name.Constant),
            (r'\b(?<!\.)((?!True)(?!False)[A-Z]\w*)\b', Name.Class),
            (r'(?<=:)\s*type', Name.Class),
            (r'((?<=function\s)|(?<=method\s)|(?<=subscript\s))\w+', Name.Function),
            (r'\".+?\"', String),
            (r"'.+?'", String),
            (r'//[^\n]*\n', Comment.Single),
            (r"/\*(?:.|\n)*?\*/", Comment.Multiline)
        ]
    }