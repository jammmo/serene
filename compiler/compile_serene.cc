#include <iostream>
#include <string>
#include <assert.h>
#include "yaml-cpp/yaml.h"

using std::cout;
using std::endl;
using std::string;

enum Accessor {LOOK, MUTATE, MOVE, COPY};

class LiteralNode {
public:
    YAML::Node yaml;

    string to_output_code() {
        return yaml.begin()->second.as<string>();
    }
};

class BaseExpressionNode {
public:
    YAML::Node yaml;

    string to_output_code() {
        if (yaml.size() == 1) {
            if (yaml[0].begin()->first.as<string>() == "literal") {
                auto a = LiteralNode();
                a.yaml = yaml[0].begin()->second;
                return a.to_output_code();
            }
        }
        return "";
    } 
};

class TermNode {
public:
    YAML::Node yaml;

    string to_output_code() {
        if (yaml.size() == 1) {
            if (yaml[0].begin()->first.as<string>() == "base_expression") {
                auto a = BaseExpressionNode();
                a.yaml = yaml[0].begin()->second;
                return a.to_output_code();
            }
        }
        return "";
    }
};

class ExpressionNode {
public:
    YAML::Node yaml;

    string to_output_code() {
        if (yaml.size() == 1) {
            if (yaml[0].begin()->first.as<string>() == "term") {
                auto a = TermNode();
                a.yaml = yaml[0].begin()->second;
                return a.to_output_code();
            }
        }
        return "";
    }
};

class ParameterNode {
public:
    string name;
    YAML::Node type;
    Accessor accessor;
};

class StatementNode {
public:
    enum Type {Print,
               Var,
               Const,
               Set,
               Run,
               Return,
               Break,
               Continue,
               While,
               For,
               If,
               Match};

    Type type;
    string output_code;

    static Type type_from_string(string s) {
        if (s == "print_statement") return Print;
        else if (s == "var_statement") return Var;
        else if (s == "const_statement") return Const;
        else if (s == "set_statement") return Set;
        else if (s == "run_statement") return Run;
        else if (s == "return_statement") return Return;
        else if (s == "break_statement") return Break;
        else if (s == "continue_statement") return Continue;
        else if (s == "while_loop") return While;
        else if (s == "for_loop") return For;
        else if (s == "if_block") return If;
        else if (s == "match_block") return Match;
        else assert(false); // should never happen
    }
};

class FunctionNode {
public:
    string name;
    std::vector<ParameterNode> parameters;
    std::vector<StatementNode> statements;
    string output_code;
};

auto create_map(YAML::Node node) {
    assert(node.IsSequence());  // This should be called on a YAML::Node sequence
    std::map<string, YAML::Node> M;

    for (auto i = 0; i < node.size(); i++) {
        auto child = node[i];   // child is a YAML::Node map with one element
        auto child_name = child.begin()->first.as<string>();
        if(M.count(child_name)) {
            assert(false);      // This function should only be used when all children are uniquely named
        } else {
            M[child_name] = child.begin()->second; // value is a YAML::Node sequence
        }
    }
    return M;
}

int main() {
    YAML::Node parsed = YAML::LoadFile("../parsed.yaml");

    auto myfunctions = parsed[0]["functions"];   // Sequence of all functions

    for (auto i = 0; i < myfunctions.size(); i++) {
        auto func_seq = myfunctions[i]["function"];  // Sequence of elements of i'th function
        auto func_map = create_map(func_seq);        // std::map of elements of i'th function

        auto F = FunctionNode();
        if (func_map.count("identifier")) {
            F.name = func_map.at("identifier").as<string>();
        }

        if (func_map.count("function_parameters")) {
            auto params = func_map.at("function_parameters");

            for (auto j = 0; j < params.size(); j++) {
                auto P = ParameterNode();
                
                auto param_seq = func_map.at("function_parameters")[j]["function_parameter"];    // Sequence of elements of j'th parameter
                auto param_map = create_map(param_seq);                                          // std::map of elements of j'th parameter
                
                if (param_map.count("accessor")) {
                    auto accessor = param_map.at("accessor").as<string>();
                    if (accessor == "mutate") {
                        P.accessor = MUTATE;
                    } else if (accessor == "move") {
                        P.accessor = MOVE;
                    } else if (accessor == "copy") {
                        P.accessor = COPY;
                    } else {
                        assert(false); //invalid accessor
                    }
                } else {
                    P.accessor = LOOK;
                }

                if (param_map.count("identifier")) {
                    P.name = param_map.at("identifier").as<string>();
                }

                if (param_map.count("type")) {
                    P.type = param_map.at("type");
                }

                F.parameters.push_back(P);
            }
        }
        
        if (func_map.count("statements")) {
            auto statements = func_map.at("statements");

            for (auto j = 0; j < statements.size(); j++) {
                auto S = StatementNode();
                
                auto statement_seq = func_map.at("statements")[j]["statement"];                 // Sequence of elements of j'th statement
                auto statement_type_str = statement_seq[0].begin()->first.as<string>();
                StatementNode::Type statement_type = StatementNode::type_from_string(statement_type_str);
                auto statement_inner_seq = statement_seq[0].begin()->second;                    // ex: map of elements from inside <print_statement>
                
                string output_code = "";
                switch (statement_type) {
                    case StatementNode::Print: {
                        output_code = "cout ";
                        for (auto k = 0; k < statement_inner_seq.size(); k++) {
                            auto E = ExpressionNode();
                            E.yaml = statement_inner_seq[k]["expression"];
                            output_code.append("<< ");
                            output_code.append(E.to_output_code());
                        }
                        output_code.append(" ;\n");
                        break;
                    }
                    case StatementNode::Var: {
                        break;
                    }
                    case StatementNode::Const: {
                        break;
                    }
                    case StatementNode::Set: {
                        break;
                    }
                    case StatementNode::Run: {
                        break;
                    }
                    case StatementNode::Return: {
                        break;
                    }
                    case StatementNode::Break: {
                        break;
                    }
                    case StatementNode::Continue: {
                        break;
                    }
                    case StatementNode::While: {
                        break;
                    }
                    case StatementNode::For: {
                        break;
                    }
                    case StatementNode::If: {
                        break;
                    }
                    case StatementNode::Match: {
                        break;
                    }
                }

                S.output_code = output_code;
                F.output_code.append(output_code);
            }
        }
        cout << F.output_code << endl;
    }
}