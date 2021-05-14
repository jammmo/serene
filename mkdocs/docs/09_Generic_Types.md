# 9. Generic Types
We've already seen generic types when working with arrays and vectors, but here we'll learn how they work and how to define new ones.

As we saw with generic functions, the idea behind generics is that you can define a broad template for how something works without specifying exact types, and then you can provide the type information later. We will introduce generic types through two examples using Regions and Handles.

## Implementing Regions and Handles

Serene does not have references or pointers. So how does one object refer to another object? The idiom that is most commonly used in Serene is region-based memory management, with the types `Region` and `Handle`.

If you have a bunch of objects of the same type that all refer to each other (say, in a data structure like a linked list), then the typical way to handle it is to store all of the objects inside one `Region`.  Then an object can access another object by storing its `Handle` in one of its fields. The other object would be accessed with an indexing operator, like `my_region[my_handle]`. Note that the indexing operator returns a `maybe` type here because it is possible that there is no valid object for that handle.

`Region` and `Handle` are part of the standard library, but here's a sample of how they could be implemented.

```serene
type Handle{MyRegion: type} with
~ constructor(MyRegion: type, index: Int) {
    var self.index private = index
}
~ friend Region

// Issue: should Handles be nullable?


type Region{T: type} with
~ constructor(T: type) {
    var self.vector private = Vector(Option{T})
}
~ specifics {
    method add(new_value: T) -> Handle{Region{T}} {
        run self.vector.append(NewValue)
        const handle = Handle(Region{T}, vector.length - 1)
        return handle
    }

    method delete(index_to_delete: Handle{Region{T}}) {
        set self.vector[index_to_delete] = None
    }
    
    // Implements the indexing operator on this type
    subscript get(my_handle: Handle{Region{T}}) -> Option{T} {
        return self.vector[my_handle.index]
    }
}
```

## Doubly Linked Lists

We've seen a singly linked list implementation, but doubly linked lists can be a bit more difficult in a language with single ownership of objects. However, Regions and Handles make this task manageable, as we can store all of the elements in a Region, and we can use Handles as indexes into that Region, so there is no need for pointers or shared mutability. We also use generics to allow you to specify the type of the data.

```serene
// Potentially some nullability (Option) issues here

type Node{MyHandle: type, Data: type} with
~ constructor(prev: Option{MyHandle}, data: Data, next: Option{MyHandle}) {
    var self.prev = prev
    var self.data = data
    var self.next = next
}

type DoublyLinkedList{Data: type} with
~ constructor(Data: type) {
	var self.nodes private = Region(Data)
    type self.Handle private = self.nodes.Handle
    var self.head_handle: Option(Handle) private = None
    var self.tail_handle: Option(Handle) private = None
}

~ specifics {
    method addFirst(a: Data) {
        set self.head_handle = self.nodes.add!(Node(None, a, self.head_handle))
    }

    method addLast(a: Data) {
        set self.tail_handle = self.nodes.add!(Node(self.tail_handle, a, None))
    }

    method deleteFirst() {
        if (self.head_handle is None) return
        const x = self.head_handle
        match (self.nodes[self.head_handle].next) {
        	Some(y) -> set self.head_handle = y
        	None -> return
        }
        run self.nodes.delete!(x)
    }

    method deleteLast() {
        if (self.tail_handle is None) return
        const x = self.tail_handle
        match (self.nodes[self.tail_handle].prev) {
        	Some(y) -> set self.tail_handle = y
        	None -> return
        }
        run self.nodes.delete!(x)
    }
    
    subscript get(h: Handle) -> Option{Data} {
        match (self.nodes[h]) {
        	Some(x) -> return x.data
        	None -> return None
        }
    }
}
```