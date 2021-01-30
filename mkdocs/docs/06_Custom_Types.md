# 6. Custom Types

Types in Serene can be defined using the `type` keyword, as shown below. Serene supports multiple forms of "compound types", including structs, enums, and tuples.

```
type Person is struct {
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

type Point3D is tuple {
    Int,
    Int,
    Int
}

type Address is tuple {
    Int,    // House number
    String, // Street name
}

type RainbowColors is enum {
    Red,
    Orange,
    Yellow,
    Green,
    Blue,
    Purple
}
```

