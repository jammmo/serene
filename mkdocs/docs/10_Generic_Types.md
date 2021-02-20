# 10. Generic Types
We will introduce generic types through a new implementation of linked lists, followed by an example using Regions and Handles, two commonly used built-in types.

## More Linked Lists

Here is a linked list implementation similar to the one we've seen before, except now it uses generics to allow you to specify the type of the data.

```serene
type Node{N: type, A: type} struct {
    data: A,
    next: N,
}

type LinkedList{A: type} with
~ constructor(first: A) {
    type self.Handle private = nodes.Handle
    var self.head private = nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: A) {
        set head = nodes.add!(Node(a, head))
    }

    method addLast(a: A) {
        if (head is Empty) {
            set head = nodes.add!(Node(a, None))
        }
        else {
            var x = nodes[head]
            while (nodes[x.next] is defined) {
                set x = nodes[x.next]
            }
            set x.next = nodes.add!(Node(a, None))
        }
    }

    method deleteFirst() {
        if (head is Empty) return
        const x = head
        set head = nodes[head].next
        run nodes.delete!(x)
    }

    method deleteLast() {
        if (head is Empty) return
        var x = nodes[head]
        while (nodes[x.next] is defined) {
            set x = nodes[x.next]
        }
        run nodes.delete!(x)
    }
    
    subscript get(MyHandle: Handle) -> maybe X {
        return nodes[MyHandle]
    }
}
```

## Regions and Handles

Serene does not have references or pointers. So how does one object refer to another object? The idiom that is most commonly used in Serene is region-based memory management, with the types `Region` and `Handle`.

If you have a bunch of objects of the same type that all refer to each other (say, in a data structure like a linked list), then the typical way to handle it is to store all of the objects inside one `Region`.  Then an object can access another object by storing its `Handle` in one of its fields. The other object would be accessed with an indexing operator, like `my_region[my_handle]`. Note that the indexing operator returns a `maybe` type here because it is possible that there is no valid object for that handle.

Below is a reference implementation of the `Region` and `Handle` types.

```serene
// Potential implementation of the Region and Handle system as a standard library module

type Handle{MyRegion: type} with
~ constructor(MyRegion: type, index: Int) {
    var self.index private = index
}
~ friend Region


type Region{T: type} with
~ constructor(T: type) {
    var self.vector private = Vector{T}()
    type self.R private = typeof(self)
}
~ specifics {
    method add(new_value: T) -> Handle{R} {
        run self.vector.append(NewValue)
        const handle = Handle(Region, vector.length)
        return handle
    }

    method delete(index_to_delete: Handle{R}) {
        run self.vector.pop!(index_to_delete)
    }
    
    subscript get(my_handle: Handle{R}) -> maybe T {
        return self.vector[my_handle.index]
    }
}
```
