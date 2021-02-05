# 1. Functions

Every program in Serene is required to have a `main` function. Here is a basic example of a `main` function that prints "Hello world!" on a new line.

``` serene
function main() {
    run printLine("Hello world!")
}
```

Here, "Hello world!" is being passed as a parameter to the `printLine` function. In Serene, the body of a function is a sequence of statements, each beginning with a keyword. `printLine` on its own isn't a statement, but we use the `run` keyword to execute it. Let's define another function that takes a parameter and also returns a value. Note that the types of both the parameters and return values must be specified.

```serene
function invert(b: Bool) -> Bool {
	return (not b)
}

function main() {
	run invert(True)			//return value is discarded
	run printLine(invert(True)) //return value is passed to printLine
}
```

