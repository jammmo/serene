# 8. Interfaces

When writing a function, sometimes you only care about what methods the function arguments support, and not how they're implemented. You may want to write the function in a flexible way so that they can accept any type that implements the correct methods. That can be done with Interfaces. Here is an example of how you can define an Interface.

```serene
import AddressModule


interface Card with
~ struct {
    returnAddress: String
}


interface Invitation with
~ struct {
    date: String,
    location: Address,
    numGuests: Int,
    accepted: Bool
}
~ signatures {
    method send(recipient: Person),
    method accept(guests: Int)
}


type WeddingInvitation with
~ struct {
    bride: String,
    groom: String,
    struct from Invitation,
    struct from Card
}
~ specifics (implements Invitation) {
    method send(recipient: Person) {
        run recipient.receive(copy self)
    }

    method accept(guests: Int) {
        set self.accepted = True
    }

    method parseLocation(address: String) from AddressModule
}



// Interfaces with generics?

interface CompareAndIndex(self: type X) with
~ signatures {
    method lessThan(other: X) -> bool
    method greaterThan(other: X) -> bool

    subscript get(index: Int) -> Option(X)
}
~ specifics where X: Array[Int] {
    method lessThan(other: Array[Int]) {
        for (i = 0, min(self.length, other.length)) {
            if (self[i] != other[i]) {
                return self[i] < other[i]
            }
        }
        return self.length < other.length
    }

    method lessThan(other: Array[Int]) {
        for (i = 0, min(self.length, other.length)) {
            if (self[i] != other[i]) {
                return self[i] > other[i]
            }
        }
        return self.length > other.length
    }

    subscript get(index: Int) -> Optional[Int] from Index(self: Array[type X])
}
```

