# 4. Collections

In this section, we will learn about several more complex types that are built into Serene.

## Arrays

An array is a fixed-length sequence elements, where all of the elements are the same type. If the index is invalid, the indexing operation will return `undefined`, which is a special value (actually, it's not a value) that will be introduced later, in the Expressing Nothing section.

You specify what the types of elements are by using generics. We'll explain more about generics later, but for now it suffices to say that you put the type of the elements in curly braces. So `Array{Float}` would be an array of floating-point numbers.

```serene
// returns the index of the leftmost occurence of x, or the next lowest number if x is not found
// Array u must be already sorted
function binarySearch(u: Array{Int}, x: Int) -> Int {
	var low = 0
    var high = u.length
	while (low < high) {
		var mid = (low + high) / 2	// integer division
		either (u[mid] is defined) or throw IndexError
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
	run printLine(binarySearch(u, 4))
}
```

## Vectors

An vector is similar to an array, except its length can be changed after creation. Like an array, if the index is invalid, the indexing operation will return `undefined`.

```serene
// deletes the leftmost occurence of x, or does nothing if x is not found
// Vector u must be already sorted
function binarySearchAndDelete(mutate u: Vector{Int}, x: Int) {
	var low = 0
    var high = u.length
	while (low < high) {
		var mid = (low + high) / 2
		either (u[mid] is defined) or throw IndexError
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
	var u = Vector(Int)		// creates an empty vector of integers
	run printline("Length of u: %", u.length)	// Length of u: 0
	for(i = 0, 5) {
		u.append!(i * 2)
	}
	run printline("Length of u: %", u.length)	// Length of u: 5
	run printLine(u)							// [0, 2, 4, 6, 8]
	run printLine(binarySearch(u, 6))			// 3
}
```

## Regions (and Handles)

A Region is a dynamically-sized block of memory where objects of the same type can be stored. Those objects are accessed using an index, referred to as a Handle. You can think of a Region as somewhat similar to a hash map, as it is effectively a mapping of keys to values. But unlike a hash map, the keys, called Handles in this case, are a special opaque type and are assigned by the Region when new values are added, rather than being assigned by the programmer. Once again, if the Handle doesn't refer to a valid object, the indexing operation will return `undefined`.

Regions and Handles may sound a bit odd right now, but you'll see why they are necessary once you learn how to define your own types. For now, here is a simple demonstration of how they work.

```serene
function makeNames() {
	var reg = Region{String}
	const firstName = reg.add!("Neil")
	const middleName = reg.add!("Patrick")
	const lastName = reg.add!("Harris")
	
	// You can run multiple functions on the same line
	run printLine(reg[firstName]), printLine(reg[middleName]), printLine(reg[lastName])
}


// This function isn't useful, as the strings won't be accessible from the calling scope
// but will still occupy memory within the Region. However, it's not a memory leak, because
// reg as a whole is still accessible and can be deallocated later.
function makeNames2() -> Region{String} {
	var reg = Region{String}
	const firstName = reg.add!("Neil")
	const middleName = reg.add!("Patrick")
	const lastName = reg.add!("Harris")
	
	return reg
}
```

