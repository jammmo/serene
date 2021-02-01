# 5. Control Flow

So far, we have learned several key components to how programs are structured in Serene. However, it would be hard to implement anything practical with only what we have shown so far, as we haven't shown much of the logic necessary for describing any form of procedure. Here we discuss the control flow constructs that enable us to write practical programs.

## Conditional Statements

A conditional statement (or an if/else statement) allows a program to check a condition and do something different based on the value of that condition.

```serene
function absoluteValue(x: Int) {
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
		if (u[i] > max) {	// Do you need to check if u[i] is None?
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

## Either

Here is an example of using the indexing operator on a `Handle`. To deal with the `Option` type that is returned, we use the `either` construct. `either` will try to execute the statement in parentheses, and if any part of it returns `None`, then it will stop executing that statement (in this case, it would stop without mutating `currentObject`) and it would instead execute the second statement, after the keyword `or`.

```serene
// Assume that the LinkedList struct redirects its subscripting to LinkedList.objects

function findTail(u: LinkedList) -> Handle {
    either (var currentObject = u[u.head]) or return None
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

