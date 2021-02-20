# 10. Generic Types
We will introduce generic types through a new implementation of linked lists, followed by an example using Regions and Handles, two commonly used standard library types.

## More Linked Lists

Here is a linked list implementation similar to the one we've seen before, except now it uses generics to allow you to specify the type of the data.

```serene
type Node{MyHandle: type, Data: type} with
~ constructor(data: Data, next: MyHandle) {
    var self.data = data
    var self.next = next
}

type LinkedList{Data: type} with
~ constructor(first: Data) {
	var self.nodes private = Region(Data)
    type self.Handle private = self.nodes.Handle
    var self.head private = self.nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: Data) {
        set self.head = self.nodes.add!(Node(a, self.head))
    }

    method addLast(a: Data) {
        if (self.head is Empty) {
            set self.head = self.nodes.add!(Node(a, None))
        }
        else {
            var x = self.nodes[self.head]
            while (self.nodes[x.next] is defined) {
                set x = self.nodes[x.next]
            }
            set x.next = self.nodes.add!(Node(a, None))
        }
    }

    method deleteFirst() {
        if (self.head is Empty) return
        const x = self.head
        set self.head = self.nodes[self.head].next
        run self.nodes.delete!(x)
    }

    method deleteLast() {
        if (self.head is Empty) return
        var x = self.nodes[self.head]
        while (self.nodes[x.next] is defined) {
            set x = self.nodes[x.next]
        }
        run self.nodes.delete!(x)
    }
    
    subscript get(h: Handle) -> maybe Data {
        return self.nodes[h]
    }
}
```

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
