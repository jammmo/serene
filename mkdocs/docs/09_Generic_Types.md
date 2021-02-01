# 9. Generic Types
We will introduce generic types through an example using Regions and Handles, two commonly used built-in types.

## Regions and Handles

Serene does not have references or pointers. So how does one object refer to another object? The idiom that is most commonly used in Serene is region-based memory management, with the types `Region` and `Handle`. A `Region` is a dynamically-sized block of memory where objects of the same type can be stored. Those objects are accessed using an index, referred to as a `Handle`.

If you have a bunch of objects of the same type that all refer to each other (say, in a data structure like a linked list), then the typical way to handle it is to store all of the objects inside one `Region`.  Then an object can access another object by storing its `Handle` in one of its fields. The other object would be accessed with an indexing operator, like `my_region[my_handle]`. Note that the indexing operator returns an `Option` type here because it is possible that there is no valid object for that handle.

Below is a reference implementation of the `Region` and `Handle` types.

```serene
// Potential implementation of the Region and Handle system as a standard library module

type Handle with
~ constructor(type MyRegion, index: Int) {
    set index = index
}
~ struct {
    index: Int private
}
~ friend Region

// Handle has two parameters here, but only one is needed for the generic?


type Region with
~ constructor(type T) {
    set vector = Vector[T]
    type R = typeof(self)
}
~ struct {
    vector: Vector[T] private,
}
~ specifics {
    method add(new_value: T) -> Handle[R] {
        run vector.append(NewValue)
        const handle = Handle(Region, vector.length)
        return handle
    }

    method delete(index_to_delete: Handle[R]) {
        run vector.pop!(index_to_delete)
    }

    subscript get(my_handle: Handle[R]) -> Optional[T] {
        return vector[my_handle.index]
    }
}

// Note that all T's here are the same and they come from the constructor. Need a better way to make that clear...
```

