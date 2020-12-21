const fs = require('fs');
const { exec } = require("child_process");
const path = require("path");
const { exit } = require('process');

const nearley = require("nearley");
const dictGrammar = require("./dictionary.js");

if (process.argv.length >= 3) {
    var file = process.argv[2];
} else {
    console.log("Incorrect arguments...");
    exit(1);
}

let filetitle = path.parse(file).name;
let filefolder = path.parse(file).dir;
if (path.parse(file).ext === '.d') {
    console.log("Bad file type...");
    exit(1);
}

var text = fs.readFileSync(path.join(__dirname, file), 'utf8');

text = text.replace(/^( *)for( *\( *\w+ *;)/mg, "$1foreach$2");

text = text.replace(/(?<=(?:choice|backup) *\(.*\) *)and(?= *\(.*:)/mg, "&&");
text = text.replace(/(?<=(?:choice|backup) *\(.*\) *)and(?= *\(.*:)/mg, "||");

text = text.replace(/(?<=^function \w+\([^\n\)]*)\w[^,\n\)]*/mg, (match) => {
    if (match.startsWith('out ')) {
        return match.replace('out ', 'ref ');
    } else if (match.startsWith('copy ')) {
        return match.replace('copy ', 'in ');
    }
    else {
        return "const " + match;
    }
});

text = text.replace(/(?<=^function \w+)\([^\n\)]*Type(?=[\[ ])/mg, "(Type) $&")

text = text.replace(/(^\s*)(var)( .+)/mg, "$1auto$3")
           .replace(/(^\s*)(for\s?\()(var)( .+)/mg, "$1$2auto$4")
           .replace(/^function(?= \w+\()/mg, "auto");

text = text.replace(/(^\s*)(auto \w+ *= *)([_a-zA-Z]\w*)( *;)/mg,
                    '$1mixin("$2", __traits(compiles, $3.length) ? "$3.dup" : "$3", ";");');


text = text.replace('auto main()', 'void main()');

text = text.replace(/^( *)choice( *[^:\n]+):/mg, "$1if$2");
text = text.replace(/^( *)backup( *[^:\n]+):/mg, "$1else if$2");
text = text.replace(/^( *)default( *):/mg, "$1else$2");

text = text.replace(/^( *)Mixed\[str\] \w+ = \[[^;]+\];/mg, (x, whites) => {
    const parser = new nearley.Parser(nearley.Grammar.fromCompiled(dictGrammar));
    parser.feed(x.trimStart());
    const parsed = parser.results[0];
    let expanded = [];
    expanded.push(parsed[0] + ' ' + parsed[1] + ';\n');
    let i = 1;
    while(i < parsed[3].length) {
        expanded.push(parsed[1] + `[${JSON.stringify(parsed[3][i][0])}]` + ' = ' + parsed[3][i][2] + ';\n'); 
        i += 2;
    }
    return whites + expanded.join(whites);
});

text = "import std.stdio : print = writeln;\nimport std.variant : Mixed = Variant;\nimport std.meta : Alias;\nalias str = string;\n\n" + text;

fs.writeFileSync(path.join(__dirname, filefolder, filetitle + '.d'), text);

exec(`(cd ${filefolder} && dmd ${filetitle + '.d'})`, (error, stdout, stderr) => {
    if (error) {
        console.log(`error:\n${error.message}`);
        return;
    }
    if (stderr) {
        console.log(`stderr:\n${stderr}`);
        return;
    }
    if (stdout.replace(/\s/g, '').length) {
        console.log(`stdout:\n${stdout}`);
    }
});
