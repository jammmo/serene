# 4. Collections

In this section, we will learn about several more complex types that are built into Serene.

## Arrays

An array is a fixed-length sequence elements, where all of the elements are the same type. If the index is invalid, the indexing operation will return `undefined`, which is a special value (actually, it's not a value) that will be introduced later, in the Expressing Nothing section.

You specify what the types of elements are by using generics. We'll explain more about generics later, but for now it suffices to say that you put the type of the elements in curly braces. So `Array{Float}` would be an array of floating-point numbers.

```serene
function binarySearch(u: Array{Int}, x: Int) -> Int {
	var i = u.length / 2
	while (True) {
		either (u[i] is defined) or throw IndexError
		if (u[i] < x) {
			set i = i / 2
		} elseif (u[i] > x) {
			set i = (i + u.length)/2
		} else {
			return i
		}
	}
}

//Where is the maybe-checking?
```

## Vectors

An vector is similar to an array, except its length can be changed after creation. Like an array, if the index is invalid, the indexing operation will return `undefined`.

```serene
function binarySearchAndDelete(mutate u: Array{Int}, x: Int) {
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

//Where is the maybe-checking?
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

