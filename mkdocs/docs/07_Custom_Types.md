# 7. Custom Types

Types in Serene can be defined using the `type` keyword, as shown below. Serene supports multiple forms of "compound types", including structs, enums, and tuples.

```serene
type Person struct {
    age: Int,
    name: String,
    gender: enum {
        Male,
        Female
    },
    nickname: enum {
        Some (String),
        None
    },
}

type Point3D tuple {
    Int,
    Int,
    Int
}

type Address tuple {
    Int,    // House number
    String, // Street name
}

type RainbowColors enum {
    Red,
    Orange,
    Yellow,
    Green,
    Blue,
    Purple
}
```



## Linked List Example

Here is an example of a singly linked list implementation in Serene. Notice here that the definition of the `LinkedList` type has multiple parts to it: a struct, a constructor, and specifics. The struct is the "format" of the data that is stored within the type (it can also be an enum or tuple), while the constructor initializes the struct to actual values. `specifics` is used to implement methods that can be called on this type. When a type definition has multiple parts like this, each part begins with a tilde (`~`), and they are meant to look like a bulleted list of details about the type.

```serene
// Linked list of integers

type Node(type N) struct {
    data: Int,
    next: N,
}

type LinkedList with
~ struct {
    nodes: Region[Node[Int]],
    head: Cell[Handle],
}

~ constructor(first: Int) {
    type Handle = nodes.Handle
    set head = nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: Int) {
        set head = nodes.add!(Node(a, head))
    }

    method addLast(a: Int) {
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
    
    subscript get(MyHandle: Handle) -> maybe Int {
        return nodes[MyHandle]
    }
}
```