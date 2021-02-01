# Example: Linked List
Here is an example of a singly linked list implementation in Serene:

```serene
type Node(type N) struct {
    data: Int,
    next: N,
}

type LinkedList with
~ struct {
    nodes: Region(Node),
    Handle: Type private,
    head: Handle,
}

~ constructor(first: Int) {
    set self.nodes = Region(Node)
    set self.Handle = nodes.Handle
    set self.head = nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: Int) {
        set self.head = nodes.add!(Node(a, self.head))
    }

    method addLast(a: Int) {
        if (self.head == None) {
            set self.head = nodes.add!(Node(a, None))
        }
        else {
            var x = nodes[self.head]
            while (x.next != None) {
                set x = nodes[x.next]
            }
            set x.next = nodes.add!(Node(a, None))
        }
    }

    method deleteFirst() {
        if (self.head == None) return
        const x = self.head
        set self.head = nodes[self.head].next
        run nodes.delete!(x)
    }

    method deleteLast() {
        if (self.head == None) return
        var x = nodes[self.head]
        while (x.next != None) {
            set x = nodes[x.next]
        }
        run nodes.delete!(x)
    }
}
```

