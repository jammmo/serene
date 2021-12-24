#use Grammar::Tracer;

my $original;

grammar Serene {
    # Error reporting
    method error($message) {
        note "COMPILE ERROR:";
        if ($message eq "") {
            my $line = $*LAST + 1;
            if $line > $original.lines.elems {
                note "Invalid syntax at end of file.";
                exit(1);
            }

            my $text = $original.lines[$line - 1].trim();

            until $text.contains(/\w/) {
                $line += 1;
                if $line > $original.lines.elems {
                    note "Invalid syntax at end of file.";
                    exit(1);
                }
                $text = $original.lines[$line - 1].trim();
            }
            note "Invalid syntax at line number ", $line , ":";
            note "  - Code: ``` ", $text, " ```";
            note "";
        } else {
            my $line = line_num(self.pos);
            note "Invalid syntax at line number ", $line , ":";
            note "  - Code: ``` ", $original.lines[$line - 1].trim(), " ```";
            note "  - ", $message;
            note "";
        }
        exit(1);
    }

    # File structure and whitespace
    rule TOP {
        :my Int $*LAST = 0;
        ^ [ <.separator>? <definitions> <.separator>? || <error("")> ] $
    }
    token ws {
        <!ww> \h* 
    }
    token separator {
        [ <line_separator> | <end_separator> ] { $*LAST = max(line_num(self.pos), $*LAST) }
    }
    token line_separator {
        [ \h* <.comment>? \v ]+ \h*
    }
    token end_separator {
        [ \h* <.comment>? \v ]* [ \h* <.comment>? $ ]
    }
    token comma_sp {
        ',' <separator>?
    }
    token comment {
        [ <line_comment> | <multiline_comment> ] { $*LAST = max(line_num(self.pos), $*LAST) }
    }
    token line_comment {
        '//' \V* $$
    }
    token multiline_comment {
        "/*" .*? "*/" $$
    }

    # Main language grammar
    token definitions {
        [ <function> || <struct_definition> || <include_statement> || [ <var_statement> || <const_statement>] <error("Global variables are not allowed.")> ]* %% <.separator>
    }
    token statements {
         <statement>* %% [ <.separator> || <.ws> ';' <error("Statements are terminated with newline characters, not semicolons.")> ]
    }
    token statement {
        [ <print_statement>
        | <var_statement>
        | <const_statement>
        | <set_statement>
        | <run_statement>
        | <return_statement>
        | <break_statement>
        | <continue_statement>
        | <exit_statement>
        | <while_loop>
        | <for_loop>
        | <if_block>
        | <match_block> ]
        
        || [ <function_call> <error("Function calls cannot be used as statements. Use the 'run' keyword.")> ]

        || [ <base_expression> [ <method_call> | <field_access> | <index_call> ]*? <method_call> <error("Method calls cannot be used as statements. Use the 'run' keyword.")> ]
    }

    token literal {
        [
        | <int_literal>
        | <float_literal>
        | <string_literal>
        | <char_literal>
        | <bool_literal>
        | <collection_literal>
        ]
        [ <.ws> <type_solidifier> ]?
    }
    token int_literal {
        \d+
    }
    token float_literal {
        \d+ "." \d*
    }
    token literal_punctuation {     # Does not include backslash or either type of quotes
        | ' ' | '!' | '#' | '$' | '%' | '&' | '(' | ')' | '*' | '+' | ',' | '-'
        | '.' | '/' | ':' | ';' | '<' | '=' | '>' | '?' | '@' | '[' | '~' | ']'
        | '^' | '_' | '`' | '{' | '|' | '}' 
    }
    token string_literal {
        '"' [ <.alnum> | <.literal_punctuation> | '\n' | '\\\\' | "'" | '\\"' ]* '"'
    }
    token char_literal {
        "'" [ <.alnum> | <.literal_punctuation> | '\n' | '\\\\' | '"' | "\\'" ] "'"
    }
    token bool_literal {
        'True' | 'False'
    }
    rule collection_literal {
        '['
        [ <expression>* %% <.comma_sp> ]
        ']'
    }

    rule type_solidifier {
        'as' <type>
    }

    token identifier {
        [ [ 'look' || 'mutate' || 'move' || 'copy' || 'var' || 'const' || 'set' || 'function' || 'type' ||
            'if' || 'elseif' || 'else' || 'for' || 'while' || 'break' || 'continue' || 'exit' || 'return' || 'and' || 'or' || 'not' ||
            'run' || 'match' || 'struct' || 'import' || 'private' || 'in' ]
          <|w> <error("")> ] ||         # This error should be "Cannot use reserved keyword as identifier.", however sometimes it gets mistakenly called when the error is actually something else.
        <.lower> <.alnum>*
    }

    token base_type {
        <.upper> <.alnum>*
    }
    rule type {
        | [ <base_type> 'of' <type_parameters> ]
        | [ <base_type> ]
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

    # Type definitions
    rule struct_member {
        <identifier> ':' <type>
    }

    rule struct_definition {
        'type' <base_type> 'struct' <.separator>? '{' <.separator>
        [ <struct_member> ',' <.separator> ]* [ <struct_member> <.separator> ]?
        '}'
        [ 'with' <.separator> [ <extension>+ % <.separator> ] ]?
    }

    rule extension {
        <definitions_extension> || <policies_extension>
    }

    rule definitions_extension {
        "~" 'definitions' '{' <.separator>
        <method_definitions>
        '}'
    }

    rule policies_extension {
        "~" 'policies' '{' <error("Policies are not yet supported.")>
    }

    rule method_definitions {
        [ <method_definition>* %% <.separator> ]
    }

    rule include_statement {
        'include' <file_name>
    }

    token file_name {
        [ \w || "_" || "-" || "/" ]+ '.sn'
    }

    # Function definitions and calls
    rule function {
        'function' <identifier>
        '(' <function_parameters> ')'
        [ <.separator>? 'on' <def_type_parameters> ]?
        [ <.separator>? '->' <type> ]?
        <.separator>?
        '{' <.separator>
        <statements>
        '}'
    }

    rule method_definition {
        'method' <identifier> <mutate_method_symbol>?
        '(' <function_parameters> ')'
        [ <.separator>? '->' <type> ]?
        <.separator>?
        '{' <.separator>
        <statements>
        '}'
    }

    rule function_parameters {
        <function_parameter>* %% <.comma_sp>
    }

    rule function_parameter {
        <accessor>? <identifier> [ ':' <type> || <error("Function parameter has no type specified.")> ]
    }

    token function_call {
        <identifier> '(' <function_call_parameters> ')'
    }

    rule function_call_parameters {
        <function_call_parameter>* %% <.comma_sp>
    }

    rule function_call_parameter {
        <accessor>? <expression>
    }

    token constructor_call {
        <base_type> '(' <constructor_call_parameters> ')'
    }

    rule constructor_call_parameters {
        <constructor_call_parameter>* %% <.comma_sp>
    }

    rule constructor_call_parameter {
        | [<accessor>? <expression>]
        | <type>
    }

    rule type_parameters {
        | [ <type> ]
        | [ '(' [[ <type> ]+ %% <.comma_sp> ] ')' ]
    }

    rule def_type_parameters {
        | [ 'type' <base_type> ]
        | [ '(' [[ 'type' <base_type> ]+ %% <.comma_sp> ] ')' ]
    }

    token mutate_method_symbol {
        '!'
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

    token place_term {
        <base_expression> [ <field_access> | <index_call> ]*
    }

    # Types of statements
    rule print_statement {
        'print' <expression> [ ',' <expression> ]*
    }

    rule var_statement {
        'var' <identifier> [ ':' <type> ]? [ '=' || <error("Incorrect assignment operator.")> ] <expression>
    }

    rule const_statement {
        'const' <identifier> [ ':' <type> ]? [ '=' || <error("Incorrect assignment operator.")> ] <expression>
    }

    rule set_statement {
        'set' [ <place_term> || <identifier> ]
        [ ':' <type> <error("'set' statement cannot be used with an explicit type, as the type of the variable is already assigned.")>]?
        <assignment_op> <expression>    # throw error("Incorrect assignment operator.") here?
    }

    rule run_statement {
        | 'run' <term>
    } #should all terms be allowed? 'run a.b()' is fine, but what about 'run a.b().c' or 'run a.b()[5]'?

    rule return_statement {
        [ 'return' <expression> ] | [ 'return' $$ ]
    }

    rule break_statement {
        'break'
    }

    rule continue_statement {
        'continue'
    }

    rule exit_statement {
        'exit' <int_literal>
    }

    # Blocks
    rule while_loop {
        'while' <expression> <.separator>? '{' <.separator>
        <statements>
        '}'
    }

    rule for_loop {
        | [ 'for' '(' <identifier> 'in' <expression> ')' <.separator>? '{' <.separator>
            <statements>
            '}' ]
        | [ 'for' <identifier> 'in' <expression> <.separator>? '{' <.separator>
            <statements>
            '}' ]
        | [ 'for' '(' <identifier> '=' <expression> ';' <expression> ')' <.separator>? '{' <.separator>
            <statements>
            '}' ]
        | [ 'for' <identifier> '=' <expression> ';' <expression> <.separator>? '{' <.separator>
            <statements>
            '}' ]
    }

    rule if_block {
        [ <if_branch> || <elseif_branch> <error("'elseif' branch has no corresponding 'if' branch.")> || <else_branch> <error("'else' branch has no corresponding 'if' branch.")> ]
        [ <.separator>? <elseif_branch> ]*
        [ <.separator>? <else_branch> ]?
    }

    rule if_branch {
        'if' <expression> <.separator>? '{' <.separator>
        <statements>
        '}'        
    }

    rule elseif_branch {
        'elseif' <expression> <.separator>? '{' <.separator>
        <statements>
        '}'
    }

    rule else_branch {
        'else' <.separator>? '{' <.separator>
        <statements>
        '}'
    }

    rule match_block {
        'match' '(' <expression> ')' <.separator>? '{' <.separator>
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


sub line_num ($pos) {
    my @a = $original.indices("\n");
    my $num = 1;
    for @a {
        if $pos > $_ {
            $num += 1;
        } else {
            last;
        }
    }
    return $num;
}

sub print_parsed ($match, $n_indent) {
    my $r = '';
    for $match.caps {
        if $_.key eq 'statement' {
            $r ~= "\n" ~ ( '  ' x $n_indent ) ~ "- " ~ $_.key ~ ": ";
            $r ~= "\n" ~ ( '  ' x ($n_indent + 1)) ~ "- line_number: " ~ line_num($_.value.from()) ~ print_parsed($_.value, $n_indent + 1)
        } else {
            $r ~= "\n" ~ ( '  ' x $n_indent ) ~ "- " ~ $_.key ~ ": " ~ print_parsed($_.value, $n_indent + 1);
        }
    }
    if $match.caps[0].^name eq 'Nil' {
        $r ~= "'" ~ $match.subst(/"'"/, "''", :g) ~ "'";
    }
    return $r;
}

sub MAIN($file) {
    if not $file.IO.e {
        note 'Error passing file name to parser: ', $file;
        exit(1);
    }

    $original = slurp $file;
    my $parsed = Serene.parse($original);

    my $output = print_parsed($parsed, 0);

    say $output;
}
