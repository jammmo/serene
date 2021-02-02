# Example A: Linked List
Here is an example of a singly linked list implementation in Serene:

```serene
// Linked list of integers

type Node(type N) struct {
    data: Int,
    next: N,
}

type LinkedList with
~ struct {
    nodes: Region(Node),
    head: Handle,
}

~ constructor(first: Int) {
    set nodes = Region(Node)
    type Handle = nodes.Handle
    set head = nodes.add!(Node(first, None))
}

~ specifics {
    method addFirst(a: Int) {
        set self.head = nodes.add!(Node(a, self.head))
    }

    method addLast(a: Int) {
        if (head is None) {
            set head = nodes.add!(Node(a, None))
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
        if (head is None) return
        const x = head
        set head = nodes[head].next
        run nodes.delete!(x)
    }

    method deleteLast() {
        if (head == None) return
        var x = nodes[self.head]
        while (x.next != None) {
            set x = nodes[x.next]
        }
        run nodes.delete!(x)
    }
    
    subscript get(MyHandle: Handle) -> Optional[Int] {
        return nodes[MyHandle]
    }
}
```

