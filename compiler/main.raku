#use Grammar::Tracer;

grammar Serene {
    # File structure and whitespace
    rule TOP {
        ^ <functions> $
    }
    token ws {
        <!ww> \h* 
    }
    token separator {
        \h*\v\s*
    }

    # Main language grammar
    token functions {
        [<function> | <.comment>]+ %% <.separator>
    }
    token statements {
        [<statement> <.comment> | <statement> | <.comment>]+ %% <.separator>
    }
    token statement {
        | <print_statement>
        | <var_statement>
        | <const_statement>
        | <set_statement>
        | <run_statement>
        | <return_statement>
        | <break_statement>
        | <continue_statement>
        | <while_loop>
        | <for_loop>
        | <if_block>
        | <match_block>
    }

    token literal {
        | <int_literal>
        | <string_literal>
        | <bool_literal>
    }
    token int_literal {
        \d+
    }
    token string_literal {
        '"' <-[ " ]>* '"'
    }
    token bool_literal {
        'True' | 'False'
    }

    token identifier {
        <.alpha> <.alnum>*
    }

    token base_type {
        <.upper> <.alpha>*
    }
    token type {
        | <base_type> '{' <type> '}'
        | <base_type>
    }
    token comment {
        '//' \V* $$
    }
    token assignment_op {
        | '='
        | '+='
        | '-='
        | '*='
        | '/='
        | '%='
    }

    token infix_op {
        | <comparison_op>
        | '+'
        | '-'
        | '*'
        | '/'
        | '%'
        | 'and'
        | 'or'
    }

    token comparison_op {
        | '=='
        | '>'
        | '<'
        | '>='
        | '<='
        | '!='
    }

    token unary_op {
        | '-'
        | 'not'
    }

    token accessor {
        | 'mutate'
        | 'move'
        | 'copy'
    }

    # Function definitions and calls
    rule function {
        'function' <identifier>
        '(' <function_parameters> ')'
        [ '->' <type> ]?
        '{' <.separator>
        <statements>
        '}'
    }

    rule function_parameters {
        <function_parameter>* %% ','
    }

    rule function_parameter {
        <accessor>? <identifier> ':' <type>
    }

    token function_call {
        <identifier> '(' <function_call_parameters> ')'
    }

    rule function_call_parameters {
        <function_call_parameter>* %% ','
    }

    rule function_call_parameter {
        <accessor>? <expression>
    }

    token mutate_method_symbol {
        '!'
    }

    token constructor_call {
        <base_type> '(' <function_call_parameters> ')'
    }

    token method_call {
        '.' <identifier> <mutate_method_symbol>? '(' <function_call_parameters> ')'
    }

    token field_access {
        '.' <identifier>
    }

    # Indexing with square brackets
    token index_call {
        '[' <expression> ']'
    }

    # Expressions
    rule expression {
        <unary_op>? <term> [ <infix_op> <unary_op>? <term> ]*
    }

    rule base_expression {
        | <function_call>
        | <constructor_call>
        | <identifier>
        | <literal>
        | '(' <expression> ')'
    }

    token term {
        <base_expression> [ <method_call> | <field_access> | <index_call> ]*
    }

    # Types of statements
    rule print_statement {
        'print' <expression> [ ',' <expression> ]*
    }

    rule var_statement {
        | 'var' <identifier> '=' <expression>
        | 'var' <identifier> ':' <type> '=' <expression>
    }

    rule const_statement {
        | 'const' <identifier> '=' <expression>
        | 'const' <identifier> ':' <type> '=' <expression>
    }

    rule set_statement {
        'set' <identifier> <assignment_op> <expression>
    }

    rule run_statement {
        | 'run' <function_call> 
        | 'run' <identifier> <method_call> 
    } #should term also be allowed? 'run a.b()' is fine, but what about 'run a.b().c' or 'run a.b()[5]'?

    rule return_statement {
        'return' <expression>
    }

    rule break_statement {
        'break'
    }

    rule continue_statement {
        'continue'
    }

    # Blocks
    rule while_loop {
        'while' '(' <expression> ')' '{' <.separator>
        <statements>
        '}'
    }

    rule for_loop {
        | [ 'for' '(' <identifier> 'in' <expression> ')' '{' <.separator>
            <statements>
            '}' ]
        | [ 'for' '(' <identifier> '=' <expression> ',' <expression> ')' '{' <.separator>
            <statements>
            '}' ] 
    }

    rule if_block {
        <if_branch> <.separator>?
        [ <elseif_branch> <.separator>? ]?
        [ <else_branch> <.separator>? ]?
    }

    rule if_branch {
        'if' '(' <expression> ')' '{' <.separator>
        <statements>
        '}'        
    }

    rule elseif_branch {
        'elseif' '(' <expression> ')' '{' <.separator>
        <statements>
        '}'
    }

    rule else_branch {
        'else' '{' <.separator>
        <statements>
        '}'
    }

    rule match_block {
        'match' '(' <expression> ')' '{' <.separator>
        [ <match_branch> <.separator> ]+
        '}'    
    }

    rule match_branch {
        | [ <expression> [ ',' <expression> ]* '->' '{' <.separator>
            <statements>
            '}' ]
        | [ 'else' '->' '{' <.separator>
            <statements>
            '}' ]
        | [ <expression> [ ',' <expression> ]* '->' <statement> ]
        | [ 'else' '->' <statement> ]
    }
}

sub print_parsed ($match, $n_indent) {
    my $r = '';
    for $match.caps {
        $r ~= "\n" ~ ( '  ' x $n_indent ) ~ "- " ~ $_.key ~ ": " ~ print_parsed($_.value, $n_indent + 1);
    }
    if $match.caps[0].^name eq 'Nil' {
        $r ~= "'" ~ qq[$match] ~ "'";
    }
    return $r;
}

sub MAIN($file) {
    say 'Compiling ', $file, ' now...';
    my $parsed = Serene.parsefile($file);
    my $output = print_parsed($parsed, 0);
    #say $output;
    #spurt 'parsed.yaml', $output;

    my $py = $*PROGRAM.dirname.IO.add('compile.py').absolute;
    say 'Running ', $py, "\n";

    my $py_process = run 'python', $py, :in;
    $py_process.in.say: $output;
    $py_process.in.close;
}