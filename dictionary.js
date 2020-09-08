// Generated automatically by nearley, version 2.19.5
// http://github.com/Hardmath123/nearley
(function () {
function id(x) { return x[0]; }
var grammar = {
    Lexer: undefined,
    ParserRules: [
    {"name": "ArrayAssignment", "symbols": ["Type", "_", "Name", "_", {"literal":"="}, "_", "AALiteral", "_", {"literal":";"}], "postprocess": d => d.filter(x => x !== null)},
    {"name": "Type$string$1", "symbols": [{"literal":"M"}, {"literal":"i"}, {"literal":"x"}, {"literal":"e"}, {"literal":"d"}, {"literal":"["}, {"literal":"s"}, {"literal":"t"}, {"literal":"r"}, {"literal":"]"}], "postprocess": function joiner(d) {return d.join('');}},
    {"name": "Type", "symbols": ["Type$string$1"], "postprocess": d => d.join('')},
    {"name": "Name$ebnf$1", "symbols": [/[\w]/]},
    {"name": "Name$ebnf$1", "symbols": ["Name$ebnf$1", /[\w]/], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "Name", "symbols": ["Name$ebnf$1"], "postprocess": d => d[0].join('')},
    {"name": "AALiteral", "symbols": [{"literal":"["}, "KeyValue", {"literal":"]"}]},
    {"name": "AALiteral", "symbols": [{"literal":"["}, "KeyValue", {"literal":","}, "KeyValue", {"literal":"]"}]},
    {"name": "dqstring$ebnf$1", "symbols": []},
    {"name": "dqstring$ebnf$1", "symbols": ["dqstring$ebnf$1", "dstrchar"], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "dqstring", "symbols": [{"literal":"\""}, "dqstring$ebnf$1", {"literal":"\""}], "postprocess": function(d) {return d[1].join(""); }},
    {"name": "sqstring$ebnf$1", "symbols": []},
    {"name": "sqstring$ebnf$1", "symbols": ["sqstring$ebnf$1", "sstrchar"], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "sqstring", "symbols": [{"literal":"'"}, "sqstring$ebnf$1", {"literal":"'"}], "postprocess": function(d) {return d[1].join(""); }},
    {"name": "btstring$ebnf$1", "symbols": []},
    {"name": "btstring$ebnf$1", "symbols": ["btstring$ebnf$1", /[^`]/], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "btstring", "symbols": [{"literal":"`"}, "btstring$ebnf$1", {"literal":"`"}], "postprocess": function(d) {return d[1].join(""); }},
    {"name": "dstrchar", "symbols": [/[^\\"\n]/], "postprocess": id},
    {"name": "dstrchar", "symbols": [{"literal":"\\"}, "strescape"], "postprocess": 
        function(d) {
            return JSON.parse("\""+d.join("")+"\"");
        }
        },
    {"name": "sstrchar", "symbols": [/[^\\'\n]/], "postprocess": id},
    {"name": "sstrchar", "symbols": [{"literal":"\\"}, "strescape"], "postprocess": function(d) { return JSON.parse("\""+d.join("")+"\""); }},
    {"name": "sstrchar$string$1", "symbols": [{"literal":"\\"}, {"literal":"'"}], "postprocess": function joiner(d) {return d.join('');}},
    {"name": "sstrchar", "symbols": ["sstrchar$string$1"], "postprocess": function(d) {return "'"; }},
    {"name": "strescape", "symbols": [/["\\/bfnrt]/], "postprocess": id},
    {"name": "strescape", "symbols": [{"literal":"u"}, /[a-fA-F0-9]/, /[a-fA-F0-9]/, /[a-fA-F0-9]/, /[a-fA-F0-9]/], "postprocess": 
        function(d) {
            return d.join("");
        }
        },
    {"name": "KeyValue", "symbols": ["_", "Key", "_", {"literal":":"}, "_", "Value", "_"], "postprocess": d => d.filter(x => x !== null).flat()},
    {"name": "Key", "symbols": ["dqstring"]},
    {"name": "Value$ebnf$1", "symbols": [/[\w]/]},
    {"name": "Value$ebnf$1", "symbols": ["Value$ebnf$1", /[\w]/], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "Value", "symbols": ["Value$ebnf$1"], "postprocess": d => [d.flat().join('')]},
    {"name": "Value", "symbols": ["dqstring"], "postprocess": d => [JSON.stringify(d.flat().join(''))]},
    {"name": "Value$ebnf$2", "symbols": [/./]},
    {"name": "Value$ebnf$2", "symbols": ["Value$ebnf$2", /./], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "Value", "symbols": [{"literal":"["}, "Value$ebnf$2", {"literal":"]"}], "postprocess": d => [d.flat().join('')]},
    {"name": "_$ebnf$1", "symbols": []},
    {"name": "_$ebnf$1", "symbols": ["_$ebnf$1", /[ ]/], "postprocess": function arrpush(d) {return d[0].concat([d[1]]);}},
    {"name": "_", "symbols": ["_$ebnf$1"], "postprocess": d => null}
]
  , ParserStart: "ArrayAssignment"
}
if (typeof module !== 'undefined'&& typeof module.exports !== 'undefined') {
   module.exports = grammar;
} else {
   window.grammar = grammar;
}
})();
