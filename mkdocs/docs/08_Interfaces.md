# 8. Interfaces

When writing a function, sometimes you only care about what methods the function arguments support, and not how they're implemented. You may want to write the function in a flexible way so that they can accept any type that implements the correct methods. That can be done with Interfaces. Here is an example of how you can define an Interface.

```serene
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

    method parseLocation(address: String) from Address
}



// Interfaces with generics?

interface CompareAndIndex(self: type X) with
~ signatures {
    method lessThan(other: X) -> Bool
    method greaterThan(other: X) -> Bool

    subscript get(index: Int) -> maybe X
}
~ specifics where X: Array{Int} {
    method lessThan(other: Array{Int}) -> Bool {
        for (i = 0, min(self.length, other.length)) {
            if (self[i] != other[i]) {
                return self[i] < other[i]
            }
        }
        return self.length < other.length
    }

    method lessThan(other: Array{Int}) -> Bool {
        for (i = 0, min(self.length, other.length)) {
            if (self[i] != other[i]) {
                return self[i] > other[i]
            }
        }
        return self.length > other.length
    }

    subscript get(index: Int) -> maybe Int from Index{Array{type X}}
}
```

