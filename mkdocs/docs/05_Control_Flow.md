# 5. Control Flow

So far, we have learned several key components to how programs are structured in Serene. However, it would be hard to implement anything practical with only what we have shown so far, as we haven't shown much of the logic necessary for describing any form of procedure. Here we discuss the control flow constructs that enable us to write practical programs.

## Conditional Statements

A conditional statement (or an if/else statement) allows a program to check a condition and do something different based on the value of that condition.

```serene
function absoluteValue(x: Int) -> Int {
	if (x < 0) {
		return -x
	} else {
		return x
	}
}
```

## Loops

Serene has two looping constructs: For Loops and While Loops.

```serene
function findMax(u: Vector[Int]) -> Int {
	var max: Int = INT_MIN
	for (x in u) {
		if (x > max) {
			set max = x
		}
	}
}

function findMax2(u: Vector[Int]) -> Int {
	var max: Int = INT_MIN
	var i: Int = 0
	while (i < u.length) {
		if (u[i] > max) {	// Do you need to check if u[i] is undefined?
			set max = u[i]
		}
	}
}
```

## Match

A Match statement takes a single object as its parameter and it allows you to write multiple paths of execution based on the value of the object.

```serene
function makeChoice() -> Bool {
	while (True) {
        var input = ReadLine()
        match (input) {
            "" -> continue
            "y", "Y" -> return True
            "n", "N" -> return False
            else -> {
            	run printLine("Input is invalid, try again")
            	continue
            }
        }
	}
}
```

## More Control Flow

There is one more control flow construct in Serene, named `either`. But there's a bit of background explanation as to why `either` is necessary, so you can explore that in the next section.