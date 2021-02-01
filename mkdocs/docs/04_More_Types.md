# 4. More Types

In this section, we will learn about several more complex types that are built into Serene.

## Optionals

Optionals are used to represent values that may or may not exist. Before making use of the value, the language require you to check that the Optional is not None. This is typically done with a `match` statement or an `either` statement, which will both be introduced in the next section of this guide.

```serene
function getFirst(u: String) -> Optional[Char] {
	if (u.length > 0) {
		return u[0]
	} else {
		return None
	}
}
```

## Arrays

An array is a fixed-length sequence elements, where all of the elements are the same type. Indexing an array always returns an Optional, because the index used may be outside of the valid range of indexes. If the index is invalid, the indexing operation will return None.

```serene
function binarySearch(u: Array[Int], x: Int) -> Int {
	var i = u.length / 2
	while (True) {
		if (u[i] < x) {
			set i = i / 2
		} elseif (u[i] > x) {
			set i = (i + u.length)/2
		} else {
			return i
		}
	}
}

//Where are the Optionals?
```

## Vectors

An vector is similar to an array, except its length can be changed after creation. Like an array, indexing a vector returns an Option.

```serene
function binarySearchAndDelete(mutate u: Array[Int], x: Int) {
	var i = u.length / 2
	while (True) {
		if (u[i] < x) {
			set i = i / 2
		} elseif (u[i] > x) {
			set i = (i + u.length)/2
		} else {
			u.delete!(i)
		}
	}
}

//Where are the Optionals?
```