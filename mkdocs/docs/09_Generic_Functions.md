# 9. Generic Functions

Serene supports both generic functions and generic types. A generic parameter is specified using the `type` keyword, like in the example below.

```serene
function elementInArray{T: type} (move elem: T, arr: Array{T}) -> maybe T {
    for (i = 0, arr.length) {
        if (arr[i] == elem) {
            return elem
        }
    }

    return undefined
}

// Where statement
function elementInArray2{A: type, B type} (move elem: A, arr: B) -> maybe A where
    A: Simple,
    B: Array{A} {

    for (i = 0, arr.length) {
        if (arr[i] == elem) {
            return elem
        }
    }

    return undefined
}

function main() {
	var u = Array(1, 3, 5, 7)
	either (run printLine(elementInArray(5, u)) or run printLine("Could not be found")
	either (run printLine(elementInArray2(7, u)) or run printLine("Could not be found")
}
```

