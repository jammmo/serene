# 1. Functions

Every program in Serene is required to have a `main` function. Here is a basic example of a `main` function that prints "Hello world!" on a new line.

``` serene
function main() {
    run printLine("Hello world!")
}
```

Here, "Hello world!" is being passed as a parameter to the `printLine` function. Let's define another function that takes a parameter and also returns a value. Note that the types of both the parameters and return values must be specified.

```serene
function invert(b: Bool) -> Bool {
	return (not b)
}
```

