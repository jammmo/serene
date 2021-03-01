# 2. Variables, Types, and Math

You can store a value with either the keyword `const` (short for "constant") or the keyword `var` (short for "variable"). The value of a variable can be modified after it is created with the keyword `set`, but the value of a constant can never change. Note that variables and constants must be defined inside of functions, and they are locally scoped: that is, they are only valid in the scope in which they are declared. When that scope ends, all of its local values will be deleted and the associated memory will be freed.

```serene
function test1() {
    const age: Int = 20
    print age
    //age can't be changed here!
}

function test2() {
    var age: Int = 20
    print age
    set age = 21
    print age
    set age = age + 1
    print age
    set age += 1    //same as: set age = age + 1
    print age
}

function test3() {
    const base = 5 //the type Int is implied here
    const height = 8
    const area: Float = (1/2) * base * height
    print area, " inches"
}

function test4() {
    var name: String = "Rick Astley"
    set name = "Rickroll"   //strings are mutable
    print name
}
```

