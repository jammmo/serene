ArrayAssignment ->
    Type _ Name _ "=" _ AALiteral _ ";" {% d => d.filter(x => x !== null) %}

Type ->
    "Mixed[str]" {% d => d.join('') %}

Name ->
    [\w]:+ {% d => d[0].join('') %}

AALiteral ->
    "[" KeyValue "]"
  | "[" KeyValue "," KeyValue "]"

@builtin "string.ne"

KeyValue ->
    _ Key _ ":" _ Value _ {% d => d.filter(x => x !== null).flat() %}

Key ->
    dqstring

Value ->
    [\w]:+      {% d => [d.flat().join('')] %}
  | dqstring    {% d => [JSON.stringify(d.flat().join(''))] %}
  | "[" .:+ "]" {% d => [d.flat().join('')] %}

_ ->
  [ ]:* {% d => null %}