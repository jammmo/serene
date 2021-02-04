# 6. Expressing Nothing

There are a couple ways of expressing that something does not exist in Serene. 

## Maybe (Defined and Undefined)

The keywords `defined` and `undefined` are used primarily for checking whether an index into some collection (like a vector or a region) is valid. While the language Python, for example, throws an `IndexError` at runtime when an invalid index is accessed, Serene returns `undefined`. The compiler requires you to check for these undefined values, which allows common errors to be caught at compile time (using "type refinement") instead of  at runtime. Checking whether a value is defined is often done with `either` statement, which will be introduced below.

An important note is that `defined` and `undefined` technically aren't values. This makes them different from null pointers in C or `Option` in Rust. You can have a function return a value that might be undefined by prefixing the return type with `maybe`, but function parameters cannot be undefined. Also, once you have checked that a value is defined, you can continue to use it like any other value: there is no "unwrapping" necessary. 

```serene
function getFirst(u: String) -> maybe Char {
	if (u.length > 0) {
		return u[0]
	} else {
		return undefined
	}
}
```

## Either

The `either` statement is used to handle values that may be undefined. Here is an example of using the indexing operator with a `Handle`. `either` will try to execute the statement in parentheses, and if any part of it returns `undefined`, then it will stop executing that statement (in this case, it would stop without mutating `currentObject`) and it would instead execute the second statement, after the keyword `or`.

```serene
// Assume that the LinkedList struct redirects its subscripting to LinkedList.objects

function findTail(u: LinkedList) -> maybe Handle {
    either (var currentObject = u[u.head]) or return undefined
    while (True) {
        var currentIndex = currentObject.next
        either (set currentObject = L[currentIndex]) or return currentIndex
    }
}


function removeTail(mutate u: LinkedList) {
    either (var currentObject = u[u.head]) or return	//This copies u[u.head] so it might not be efficient
    while (True) {
        var currentIndex = currentObject.next
        either (set currentObject = u[currentIndex]) or break
    }
    run u.delete!(currentIndex)		//methods that mutate the object are called with a "!"
}
```

## Cell

While it isn't present for `maybe` types, the "unwrapping" behavior of something like `Option` in Rust is still useful in certain situations. For that, Serene provides the `Cell` type, which can be unwrapped into either `Some(x)` or `Empty`.