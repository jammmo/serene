# 6. More Types
In this section, we will learn about a built-in type called Option, and we will also see how to define our own types.


## Option

The Option type is a way of "wrapping" an object that may or may not exist. This is useful in certain situations, like when defining a recursive type such as the Node type we will see in the next section. The Option type can be unwrapped into either `Some(x)` or `None`, where x is an assignment to a variable. All the usual ownership rules still apply to Options: a Option owns whatever value it holds, so you can't have two Options holding the same value.

```serene
function printNickname(p: Person) {
    match (p.nickname) {
        Some(name) -> print "Your nickname is ", name, "."
        None -> print "No nickname is set."
    }
}
```


## Defining Types
Types in Serene can be defined using the `type` keyword, as shown below. You can use this format to define structs, enums, and tuples.

```serene
type Person struct {
    age: Int,
    name: String,
    nickname: Option{String}
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

function main() {
	var jason = Person(41, "Jason Segel", Option("Marshall"))
	set jason.nickname = None
	
	var color = RainbowColors::Red
	set color = RainbowColors::Green
}
```


## Linked List Example

Here is an example of a singly linked list implementation in Serene. Notice here that the definition of the `LinkedList` type has multiple parts to it. Internally, it stores data as a struct, but instead of passing the fields of the struct directly, the user will pass arguments to a `constructor` function which will create and initialize the struct to actual values. `specifics` is used to implement methods that can be called on this type. When a type definition has multiple parts like this, each part begins with a tilde (`~`), and they are meant to look like a bulleted list of details about the type. This format is called a "constructed type".

Another new thing here is `private` fields, which can't be accessed from outside of the type's definition. However, a type can give special permission for another type to access its private fields by declaring it a `friend` type, as we will see later.

```serene
// Linked list of integers

type Node struct {
    data: Int,
    next: Option{Node}
}

type LinkedList with
~ constructor(first: Int) {
	// To be able to represent an empty list, the head must be in an Option
    var self.head private = Option(Node(first, None))
}

~ specifics {
    method addFirst!(a: Int) {	// This method mutates the object, so the exclamation point is required
        set self.head = Node(a, move self.head)
    }

    method popFirst!() -> Option{Int} {
        if (self.head is None) return None
        var x = self.head.data	// note that this copies self.head.data
        set self.head = self.head.next
        return Some(x)
    }
    
    method append!(a: Int) {
        if (self.head is None) {
            set self.head = Node(a, None)
        }
        else {
            bind x = self.head // the head node is still owned by self.head, not x
            while (x.next is not None) {
            	// this re-binds x but it doesn't mutate anything
                bind x = x.next
            }
            // you can "set" a member of a binding (but not the binding itself)
            set x.next = Node(a, None)
        }
    }
    
    method empty() -> Bool {
    	return (self.head is None)
    }
}
```