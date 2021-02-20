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
    nickname: Cell{String}
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

Here is an example of a singly linked list implementation in Serene. Notice here that the definition of the `LinkedList` type has multiple parts to it. Internally, it stores data as a struct, but instead of passing the fields of the struct directly, the user will pass arguments to a `constructor` function which will create and initialize the struct to actual values. `specifics` is used to implement methods that can be called on this type. When a type definition has multiple parts like this, each part begins with a tilde (`~`), and they are meant to look like a bulleted list of details about the type. This format is called a "constructed type".

One new thing here is `private` fields, which can't be accessed from outside of the type's definition. However, a type can give special permission for another type to access its private fields by declaring it a `friend` type, as we will see later.

```serene
// Linked list of integers

type Node{MyHandle: type} with
~ constructor(data: Int, next: MyHandle) {
    var self.data: Int
    var self.next: MyHandle
}

type LinkedList with
~ constructor(first: Int) {
	var self.nodes private = Region(Int)
    type self.Handle private = self.nodes.Handle
    var self.head private = self.nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: Int) {
        set self.head = self.nodes.add!(Node(a, self.head))
    }

    method addLast(a: Int) {
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
    
    subscript get(h: Handle) -> maybe Int {
        return self.nodes[h]
    }
}
```