# 2. Variables, Types, and Math

A new variable can be created with either the keyword `const` (short for "constant") or the keyword `var` (short for "variable"). 

```serene
function test1() {
    const age: Int = 20
    run printLine(age)
    // age can't be changed here!
}

function test2() {
    var age: Int = 20
    run printLine(age)
    set age = 21
    run printLine(age)
    set age = age + 1
    run printLine(age)
    set age += 1    // same as: set age = age + 1
    run printLine(age)
}

function test3() {
    const base = 5 //the type Int is implied here
    const height = 8
    const area: Float = (1/2) * base * height
    run printLine(area, " inches")
}

function test4() {
    var name: String = "Rick Astley"
    set name = "Rickroll"   //strings are mutable
    run printLine(name)
}
```

