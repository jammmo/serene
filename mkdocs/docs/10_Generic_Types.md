# 10. Generic Types
We will introduce generic types through a new implementation of linked lists, followed by an example using Regions and Handles, two commonly used standard library types.

## Regions and Handles

Serene does not have references or pointers. So how does one object refer to another object? The idiom that is most commonly used in Serene is region-based memory management, with the types `Region` and `Handle`.

If you have a bunch of objects of the same type that all refer to each other (say, in a data structure like a linked list), then the typical way to handle it is to store all of the objects inside one `Region`.  Then an object can access another object by storing its `Handle` in one of its fields. The other object would be accessed with an indexing operator, like `my_region[my_handle]`. Note that the indexing operator returns a `maybe` type here because it is possible that there is no valid object for that handle.

Below is a reference implementation of the `Region` and `Handle` types.

```serene
type Handle{MyRegion: type} with
~ constructor(MyRegion: type, index: Int) {
    var self.index private = index
}
~ friend Region


type Region{T: type} with
~ constructor(T: type) {
    var self.vector private: Vector{T} = Vector()
}
~ specifics {
    method add(new_value: T) -> Handle{Region{T}} {
        run self.vector.append(NewValue)
        const handle = Handle(Region{T}, vector.length)
        return handle
    }

    method delete(index_to_delete: Handle{Region{T}}) {
        run self.vector.pop!(index_to_delete)
    }
    
    subscript get(my_handle: Handle{Region{T}}) -> maybe T {
        return self.vector[my_handle.index]
    }
}
```

## Doubly Linked Lists

We've seen a singly linked list implementation, but doubly linked lists can be a bit more difficult in a language with single ownership of objects. However, Regions and Handles make this task manageable, as we can store all of the elements in a Region, and we can use Handles as indexes into that Region, so there is no need for pointers or shared mutability. We also use generics to allow you to specify the type of the data.

```serene
type Node{MyHandle: type, Data: type} with
~ constructor(prev: MyHandle, data: Data, next: MyHandle) {
    var self.prev = prev
    var self.data = data
    var self.next = next
}

type DoublyLinkedList{Data: type} with
~ constructor(Data: type) {
	var self.nodes private = Region(Data)
    type self.Handle private = self.nodes.Handle
    var self.head_handle private = self.nodes.add!(Node(None, None, None))
    var self.tail_handle private = self.nodes.add!(Node(None, None, None))    
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
        set self.head_handle = self.nodes[self.head_handle].next
        run self.nodes.delete!(x)
    }

    method deleteLast() {
        if (self.head_handle is None) return
        const x = self.last_handle
        set self.last_handle = self.nodes[self.last_handle].prev
        run self.nodes.delete!(x)
    }
    
    subscript get(h: Handle) -> maybe Data {
        return self.nodes[h].data
    }
}
```