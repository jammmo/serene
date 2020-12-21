import std.stdio : print = writeln;
import std.variant : Mixed = Variant;
import std.meta : Alias;
alias str = string;

import std.array;

auto multiply(const int[][] A, const int[][] B) {
    assert(A[0].length == B.length);
    auto C = new int[][](A.length, B[0].length);
    foreach (i; 0 .. A.length) {
        foreach (j; 0 .. B[0].length) {
            foreach (k; 0 .. B.length) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
    return C;
}

void main() {
    auto A = [[1, 2], [1, 3]];
    auto B = [[1, 7], [-1, 2]];
    print(multiply(A, B));
}