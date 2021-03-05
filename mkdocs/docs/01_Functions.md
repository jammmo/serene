# 1. Functions

Every program in Serene is required to have a `main` function. Here is a basic example of a `main` function that prints "Hello world!" on a new line.

``` serene
function main() {
    print "Hello world!"
}
```

In Serene, the body of a function is a sequence of statements, each beginning with a keyword.  Let's define another function that takes a parameter and also returns a value. The `invert` function is pretty trivial, but it shows what a typical function signature looks like. Note that the types of both the parameters and return values must be specified.

```serene
function invert(b: Bool) -> Bool {
	return (not b)
}

function main() {
	run invert(True)			//return value is discarded
	print invert(True) 			//return value is printed
}
```

Remember that the body of a function is a sequence of statements: `invert(True)` on its own isn't a statement, so we use the `run` keyword to execute it.