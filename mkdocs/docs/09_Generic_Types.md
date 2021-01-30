# 9. Generic Types
We will introduce generic types through an example using Regions and Handles, two commonly used built-in types.

## Regions and Handles

Serene does not have references or pointers. So how does one object refer to another object? The idiom that is most commonly used in Serene is region-based memory management, with the types `Region` and `Handle`. A `Region` is a dynamically-sized block of memory where objects of the same type can be stored. Those objects are accessed using an index, referred to as a `Handle`.

If you have a bunch of objects of the same type that all refer to each other (say, in a data structure like a linked list), then the typical way to handle it is to store all of the objects inside one `Region`.  Then an object can access another object by storing its `Handle` in one of its fields. The other object would be accessed with an indexing operator, like `my_region[my_handle]`. Note that the indexing operator returns an `Option` type here because it is possible that there is no valid object for that handle.

Below is a reference implementation of the `Region` and `Handle` types.

```
// Potential implementation of the Region and Handle system as a standard library module
// Assume that array is variable length

// needs to be an Option type


type Handle with
~ constructor(type MyRegion, index: Int) {
    set self.index = index
}
~ struct {
    index: Int private
}
~ friend Region

// Handle has two parameters here, but only one is needed for the generic?


type Region with
~ constructor(type T) {
    set self.array = Array(T)
    type R = typeof(self)
}
~ struct {
    array: Array(T) private,
}
~ specifics {
    method add(NewValue: T) -> Handle(R) {
        run array.append(NewValue)
        const handle = Handle(Region, array.length)
        return handle
    }

    method delete(IndexToDelete: Handle(R)) {
        run array.pop!(IndexToDelete)
    }

    subscript get(MyHandle: Handle(R)) -> Option(T) {
        return array[MyHandle.index]
    }
}

// Note that all T's here are the same and they come from the constructor. Need a better way to make that clear...


// Which to use?
type NewType = something()
const NewType: type = something()
```

