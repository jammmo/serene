from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ['SereneLexer']

class SereneLexer(RegexLexer):
    name = 'Serene'
    aliases = ['serene']
    filenames = ['*.sn']

    tokens = {
        'root': [
            (r'\b(if|else|elseif|while|for|return|break|either|continue|match)\b', Keyword),
            (r'\b(let|set|var|const|run|import|or|and)\b', Keyword),
            (r'\b(function|method|interface|type|subscript)\b', Keyword),
            (r'\b(mut|mutate|move|copy)\b', Keyword.Type),
            (r'(?<=:)\s*\w+', Name.Class),
            (r'(?<=\)\s->\s)\w+', Name.Class),
            (r'((?<=function\s)|(?<=method\s)|(?<=subscript\s))\w+', Name.Function),
            (r'\".+\"', String),
            (r"'.+'", String),
            (r'//[^\n]*\n', Comment.Single),
            (r"/\*(?:.|\n)*?\*/", Comment.Multiline)
        ]
    }