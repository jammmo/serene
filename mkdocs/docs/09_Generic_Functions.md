# 9. Generic Functions

Serene supports both generic functions and generic types. A generic parameter is specified using the `type` keyword, like in the example below.

```serene
function elementInArray(move elem: type T, arr: Array{type T}) -> maybe type T {
    for (i = 0, arr.length) {
        if (arr[i] == elem) {
            return elem
        }
    }

    return undefined
}

// Where statement
function elementInArray(move elem: type A, arr: type B) -> maybe type A where
    type A: Simple,
    type B: Array{A} {

    for (i = 0, arr.length) {
        if (arr[i] == elem) {
            return elem
        }
    }

    return undefined
}

// Idea: plug in type variable to function instead of value to yield return type?
// Potentially some ambiguity/confusion there but definitely useful

// Is "type" needed everywhere in the signature or only the first time the name is referenced?
```

