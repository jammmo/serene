# 3. Mutability and Ownership

Serene's biggest innovation is its memory management model. In general, most high level programming languages (like JavaScript, Python, and Java) use a tracing garbage collector, while systems programming languages have traditionally relied on manual memory management. Both approaches have their disadvantages: manual memory management is more complex from the programmer's perspective and is prone to small errors that can cause serious bugs, while tracing garbage collectors can introduce runtime overhead and unpredictability that are undesirable for systems programming.

In recent years, a third approach has gained popularity: ownership.

The idea of ownership, which was pioneered by the language Rust, is that each value is owned by only one variable at a given time. When that variable goes out of scope, the value will be automatically deleted. It allows for safe and predictable memory management without the need for intervention from the programmer or from an additional runtime process. However, for Rust's borrowing system to be as versatile as the extensive feature-set of a language like C++ required Rust to adopt a similarly large and complex range of features and rules, which has led some to say that the language has a "high learning curve".

Serene takes inspiration from Rust's memory management system, but it aims to make ownership more straightforward. It does this by eliminating something that is a staple of most systems programming languages: Serene doesn't allow you to store references or pointers. There is no global sharing of state whatsoever—each value is owned by only one variable at a given time, and *it is only accessible within the scope of that variable*. This may seem limiting, but if you imagine a program's memory as simply a large global array, and that a pointer is simply a index into that array, you can start to imagine alternate ways of recreating reference-like behavior without explicit pointers or references. The simplest way, which is adopted in Serene's `Region` and `Handle` system, is to split that global array into multiple local arrays, and to pass the arrays and indexes back and forth between functions when data needs to be shared. This effectively simulates region-based memory management. When a Serene object needs to reference another object, it can store an index, or `Handle`, to the `Region` that stores the other object. And unlike a local variable with a pointer, which is essentially a locally-stored index to a globally-stored array, both Handles and Regions are local, so no sharing of state is possible without passing parameters.

Without pointers or references, program logic is much easier for a reader to follow, as you can clearly see whether any value is being mutated and where. In Serene, function parameters are passed immutably by default, but you can also create a function that will `move`, `copy`, or `mutate` its parameters, and there are keywords at both the definition site and calling site to make this behavior obvious. Serene's ownership model keeps the language simple and readable, while maintaining the low overhead and efficiency that is necessary for systems programming.

## How to Manage Mutability and Ownership

You've already seen `const`, which allows you to create a locally-scoped constant, and `var`, which allows to create a locally-scoped variable (that can be mutated with `set`). Now let's talk about the other place where mutability is important: function parameters.

When passing a value to a function, there are four ways you can do it. You need to specify which one to use both where the function is defined and where it is called, using accessor keywords. Let's look at the four different accessors one by one.

`look`: Look is the default behavior for function parameters, so there's no keyword required. It passes a value to a function immutably, meaning that the value cannot be altered anywhere in the function, regardless of whether the value you are passing is a literal value, a `var`, or a `const`. This also means that if function `a()` takes a value by `look`, function `a()` can't pass that value to a function `b()` that takes it by `mutate` or `move`. It can, however, pass that value to another function by `copy`, as copying a value leaves the original value unaffected.

`mutate`: Mutate effectively "borrows" the value from its original scope, allowing it to be mutated within the function as if it is a local variable. Once the function returns, ownership of the (now modified) value will return to the original scope. `mutate` is one of only two places that aliasing behavior (where mutating one variable also mutates another) exists in Serene. The other is `bind`, which is introduced later in this section. This behavior can be confusing in other languages (which is part of why Serene doesn't have pointers), but Serene makes the behavior explicit to the reader by requiring the keyword `mutate` both where the function is defined *and* where it is called. Note that you can't past a constant (`const`) as a `mutate` parameter, as once a constant is created, it can never be mutated. Also if function `a()` takes a value by `mutate`, function `a()` still can't pass that value to a function `b()` that takes it by `move`, as the value must still exist when the function returns.

`move`: If you've used Rust or modern C++, you've probably heard of Move semantics. `move` transfers ownership of an object from one scope to another. If you pass a variable to a function by `move`, that variable won't exist anymore when the function returns. You can move both variables and constants. If you move a variable into a function, that function will be able to mutate the variable with `set`, just as if it was declared locally.

`copy`: Copy does exactly what it sounds like: it copies the original value and passes the copied value to the function. The original value will be unaffected and it will still be owned by the original scope, while the new value will be owned by the new scope. It's worth mentioning at this point that all four of these accessors describe the user-level semantic behavior, but not necessarily the way that the program will execute at the hardware level. The Serene compiler will optimize the program, and part of that process is removing unnecessary copies. So if you pass a large object by copy but then you never mutate it, the compiler will be smart enough to not waste memory by copying the object and to just use a pointer to the original object.

```serene
function middleChar(s: String, mutate c: Char) {
    // Find the character at the middle index of a string
    const length = s.length
    const middle = Int(length / 2)
    set c = s[middle]
}

function removeChar(mutate s: String, c: Char) {
    // Remove all instances of a character in a string
    var i = 0
    while (i < s.length) {
        if (s[i] == c) {
        	// Exclamation marks are required for methods that mutate the object they act on
            run s.delete!(i)
        }
        else {
            set i += 1
        }
    }
}

function sortedCopy(copy s: String) -> String {
	run s.sort!()	// s is a copy of the original input, so the original input is not modified
	return s
}

// consumes a character array and returns it as a string
function charArrayToString(move u: Array{Char}) -> String {
	var s = ""
	for (x in u) {
		run s.append!(x)
	}
	return s
}

function main() {
    const name = "Matthew"
    var letter = ' '
    run middleChar(name, mutate letter)

    var new_name = name		// copies name
    run removeChar(mutate new_name, c)
    
	const mixed_up = "edcabfg"
	print sortedCopy(copy mixed_up)		// mixed_up is not modified
	
	var u_array = Array('h', 'e', 'l', 'l', 'o')
	var u_string = charArrayToString(move u_array)
	print typeof(u_string)	// prints String
	// u_array no longer exists here
}
```

## Bindings

There's one more concept we haven't introduced called a binding, or `bind`. A `bind` is sort of like a `var`, except it doesn't have ownership of its values. `bind` can be used to "visit" members of a data structure without needing to copy or move parts of the structure. (A `var` always owns its value, so there's no way for it to refer to a member of another object.) Since the values that you are binding to are owned within the same scope, `bind` is a form of local aliasing.

If you make a binding to an object owned by a `const`, then the binding can't be used to mutate anything. But if you make a binding to an object owned by a `var`, then you can mutate its members (but not the binding itself) with `set`. Unlike a `const`, a `bind` allows shadowing: that is, you can re-bind it to another object. It's a little hard to see the application of `bind` since we haven't learned to define new types of objects yet, but we'll see some examples later.