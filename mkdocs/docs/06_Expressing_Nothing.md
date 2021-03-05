# 6. Expressing Nothing

 In Serene, there are a couple ways of expressing that something does not exist. 

## Maybe (Defined and Undefined)

The keywords `defined` and `undefined` are used primarily for checking whether an index into some collection (like a vector or a region) is valid. While the language Python, for example, throws an `IndexError` at runtime when an invalid index is accessed, Serene returns `undefined`. The compiler requires you to check for these undefined values, which allows common errors to be caught at compile time (using "type refinement") instead of at runtime. Checking whether a value is defined is often done with `either` statement, which will be introduced below.

An important note is that `defined` and `undefined` technically aren't values (instead, one might describe them as "states" of a value). This makes them different from null pointers in C or `Option` in Rust. You can have a function return a value that might be undefined by prefixing the return type with `maybe`, but variables and function parameters cannot be undefined. So once you return a `maybe`, you are required to check whether it's defined before doing anything useful with it, but once you have checked it, you can continue to use it like any other value: there is no "unwrapping" necessary.

```serene
function getFirst(u: String) -> maybe Char {
	if (u.length > 0) {
		return u[0]
	} else {
		return undefined
	}
}

// This is equivalent to the first definition, as indexing a String (and most other collections)
// returns a "maybe" type. Note that leaving out "maybe" would cause a compile-time error
function getFirst2(u: String) -> maybe Char {
	return u[0]
}
```

## Cell

While it isn't present for `maybe` types, the "unwrapping" behavior of an object that may or may not exist is still useful in certain situations, like when defining a recursive type such as the Node type we will see in the next section. Serene provides the Cell type, which can be unwrapped into either `Some(x)` or `None`. All the usual ownership rules still apply to Cells: a Cell owns whatever value it holds, so you can't have two Cells holding the same value.

The main difference between a Cell and a `maybe` is that a Cell is an actual value, so it can be stored in a variable or passed to a function. `maybe` is mainly used by standard library types as a safety mechanism to detect indexing errors at compile time instead of runtime. But Cells can be used anywhere as an object that can hold (or not hold) another object.

```serene
function printNickname(p: Person) {
    match (p.nickname) {
        Some(name) -> print "Your nickname is ", name, "."
        None -> print "No nickname is set."
    }
}
```


## Either

The `either` statement is a control flow construct that is used in conjunction with `maybe` types. It allows you to execute a statement conditionally based on whether the values needed are defined. Here is an example of using the indexing operator with a `HashMap`. `either` will try to execute the statement in parentheses, and if any part of it returns `undefined`, then it will stop executing that statement (in this case, it would stop without mutating `map`) and it would instead execute the second statement, after the keyword `or`.

```serene
// Update the value for a key in a HashMap, only if the key is present
function updateValueAtKey(value: Float, key: String, mutate map: HashMap{String, Float}) {
	either (set map[key] = value) or return
}
```