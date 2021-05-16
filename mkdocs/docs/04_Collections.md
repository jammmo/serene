# 4. Collections

In this section, we will learn about several of the more complex types that are built into Serene. Collections hold a group of objects (typically of the same type), and you can access the elements of the collection using square brackets. Here, we'll learn about Array, Vectors, and Regions.

## Arrays

An array is a fixed-length sequence elements, where all of the elements are the same type. You specify what the types of elements are by using generics. We'll explain more about generics later, but for now it suffices to say that when describing a generic type like an array, you put the type of its elements in curly braces. So `Array{Float}` would be an array of floating-point numbers. However, generic types are still constructed like other objects, using the type's name followed by parameters in parenthesis (eg. `Array(0.1, 0.2, 0.3)`).

```serene
// returns the index of the leftmost occurence of x, or the next lowest number if x is not found
// Array u must be already sorted
function binarySearch(u: Array{Int}, x: Int) -> Int {
	var low = 0
    var high = u.length
	while (low < high) {
		var mid = (low + high) / 2	// integer division
		if (u[mid] < x) {
			set high = mid
		} else {
			set low = mid + 1
		}
	}
	return low
}

function main() {
	var u = Array(5, 1, 4, -3, 9, 0)
	run u.sort!()
	print binarySearch(u, 4)
}
```

## Vectors

An vector is similar to an array, except its length can be changed after creation.

```serene
// deletes the leftmost occurence of x, or does nothing if x is not found
// Vector u must be already sorted
function binarySearchAndDelete(mutate u: Vector{Int}, x: Int) {
	var low = 0
    var high = u.length
	while (low < high) {
		var mid = (low + high) / 2
		if (u[mid] < x) {
			set high = mid
		} else {
			set low = mid + 1
		}
	}
	if (u[low] == x) {
		run u.delete!(low)
	}
}

function main() {
	var u = Vector(Int)					// creates an empty vector of integers
	print "Length of u: ", u.length		// Length of u: 0
	for (i = 0, 5) {
		run u.append!(i * 2)
	}
	print "Length of u: ", u.length		// Length of u: 5
	print u								// [0, 2, 4, 6, 8]
	print binarySearch(u, 6)			// 3
}
```

## Regions (and Handles)

A Region is a dynamically-sized block of memory where objects of the same type can be stored. Those objects are accessed using an index, referred to as a Handle. You can think of a Region as somewhat similar to a hash map, as it is effectively a mapping of keys to values. But unlike a hash map, the keys, called Handles in this case, are a special opaque type and are assigned by the Region when new values are added, rather than being assigned by the programmer.

Regions and Handles may sound a bit odd right now, but you'll see why they are necessary once you learn how to define your own types. For now, here is a simple demonstration of how they work.

```serene
function makeNames() {
	var reg = Region(String)
	const first_name = reg.add!("Neil")
	const middle_name = reg.add!("Patrick")
	const last_name = reg.add!("Harris")
	
	print reg[first_name]
	print reg[middle_name]
	print reg[last_name]
}


// This function isn't useful, as the strings won't be accessible from the calling scope
// but will still occupy memory within the Region. However, it's not a memory leak, because
// reg as a whole is still accessible and can be deallocated later.
function makeNames2() -> Region{String} {
	var reg = Region(String)
	const first_name = reg.add!("Neil")
	const middle_name = reg.add!("Patrick")
	const last_name = reg.add!("Harris")
	
	return reg
}
```

