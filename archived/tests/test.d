import std.stdio : print = writeln;
import std.variant : Mixed = Variant;
import std.meta : Alias;
alias str = string;

import std.typecons;

auto pop(Type) (ref Type[] t) {
    Type a = t[$-1];
    t.length -= 1;
    return a;
}

auto append(Type) (ref Type[] t, const Type a) {
    t ~= a;
}

auto myTuple() {
    return tuple(4, 6.5, "Canada", [0,2,4,6,8]);
}

void main() {
    auto x = 7.5;
    auto a = [1,2,3];
    mixin("auto b = ", __traits(compiles, a.length) ? "a.dup" : "a", ";");
    print(a);
    print(a.pop());
    print(a);
    a.append(5);
    print(a);
    print(myTuple());

    Mixed[str] maybeThisWorks;
    maybeThisWorks["A"] = [1,2,3];
    maybeThisWorks["B"] = "igloo";

    print(maybeThisWorks);
}