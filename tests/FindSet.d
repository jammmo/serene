import std.stdio : print = writeln;
import std.variant : Mixed = Variant;
import std.meta : Alias;
alias str = string;

import std.stdio;
import std.array;
import std.string;

auto findMatch(const str a, const str b) {
    assert(a.length == b.length);
    char[4] m;
    foreach(i; 0 .. a.length) {
        if (a[i] == b[i]) m[i] = a[i];
        else {
            auto ab = [a[i], b[i]];
            if (ab.indexOf('0') == -1) m[i] = '0';
            else if (ab.indexOf('1') == -1) m[i] = '1';
            else m[i] = '2';
        }
    }
    return m.idup;
}

auto findSet() {
    auto line = stdin.readln();
    auto cards = line.split();
    int[str] cardCount;
    foreach(i; 0 .. cards.length) {
        auto cardI = cards[i];
        if ((cardI in cardCount) && (cardCount[cardI] == 2)) return i;
        foreach(j; 0 .. i) {
            auto cardJ = cards[j];
            if (cardI == cardJ) continue;
            str match = findMatch(cardI, cardJ);
            if (match in cardCount) return i;
        }
        if (cardI in cardCount) cardCount[cardI] += 1;
        else cardCount[cardI] = 0;
    }
    return -1;
}

void main() {
    print(findSet());
}