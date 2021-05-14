# 7. Interfaces

When writing a function, sometimes you only care about what methods the function arguments support, and not how they're implemented. You may want to write the function in a flexible way so that they can accept any type that implements the correct methods. That can be done with Interfaces. Here is an example of how you can define an Interface.

```serene
interface Invitation with
~ signatures {
    method send(recipient: Person)
    method accept(guests: Int)
}


type WeddingInvitation with
~ struct {
    bride: String,
    groom: String,
    date: String,
    location: Address,
    numGuests: Int,
    accepted: Bool
}
~ specifics (implements Invitation) {
    method send(recipient: Person) {
        run recipient.receive(copy self)
    }

    method accept(guests: Int) {
        set self.accepted = True
    }

	// Use implementation of method from a separate module
    method parseLocation(address: String) from Address	
}
```

