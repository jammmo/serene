# 8. Generic Functions

Serene supports both generic functions and generic types. What does that mean? Well, let's start with generic functions, which allow you to write a function without knowing the types of its parameters and return values in advance. You can later specify them when the function is called.

In C++, you might see generics that look something like `std::make_unique<Node>(data)`, where you pass two sets of parameters: the type information in angle brackets, and the initialization data for the constructor in parenthesis. In Serene, you use curly braces instead of angle brackets for the type parameters in the function definition, but you should never actually see both sets of parameters written together when the function is called, as the type parameters are always either inferred or passed explicitly as regular arguments. As we'll see in the next section, the same is true for generic types: you might want to create an array whose type is `Array{Int}`, but you would initialize it using its constructor (eg. `Array(1, 2, 3)`) and the type parameters would be inferred. (`Array{Int}(1, 2, 3)` is invalid syntax.)

Generic parameters are types, so they must be start with capital letters like any other type in Serene, and they are specified using the `type` keyword, like in the example below.

```serene
function elementInArray{T: type} (move elem: T, arr: Array{T}) -> Some{T} {
    for (i = 0, arr.length()) {
        if (arr[i] == elem) {
            return Some(elem)
        }
    }

    return None
}

// Where statement
function elementInArray2{A: type, B: type} (move elem: A, arr: B) -> Option{A} where
    A: Simple,
    B: Array{A} {

    for (i = 0, arr.length()) {
        if (arr[i] == elem) {
            return Some(elem)
        }
    }

    return None
}

function makeEmptyOptionVector{T: type} (T: type) -> Vector{Option{T}} {
	return Vector(Option{T})	// The constructor for vectors allows you to pass a type explicitly
}

function main() {
	var a = makeEmptyOptionVector(Int)
	print a					// Prints []
	run a.append!(None)
	print a					// Prints [None]
	run a.append!(18)
	print a					// Prints [None, 18]
	
	var u = Array(1, 3, 5, 7)
	match (elementInArray(5, u)) {
		Some(x) -> print x
		None -> print "Could not be found"
	}
	match (elementInArray2(7, u)) {
		Some(x) -> print x
		None -> print "Could not be found"
	}
}
```

