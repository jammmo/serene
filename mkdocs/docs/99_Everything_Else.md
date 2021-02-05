# Everything Else

Clearly, the topics described up to this point don't exhaust every feature necessary for a modern systems programming language. This is simply what has been designed so far. So what other features are planned for Serene?

## Concurrency

This is an important one, and it's probably the biggest unknown at this point. The concurrency system will likely be closely to mutability and ownership, since there will need to be some way of passing data between threads. It won't be as simple as putting a mutex on a shared variable, since the language doesn't have any shared mutable state to begin with. Because of this, concurrency will likely have to be native to the language rather than being a standard library module. (Also, it would benefit readability to have some kind of special syntax that makes the thread synchronization clear.) Perhaps some sort of message passing system will work, but I really haven't started researching anything yet.

## Hardware Interrupts

Just like with concurrency, I think it makes sense for the compiler to have some sort of awareness of hardware interrupts. Interrupts don't come up in regular application-level programming, but they're essential to embedded programming. In C, programming interrupt service routines often involves mutating global variables that are declared `volatile`, but in Serene that would completely break the safety and "sanity" of the ownership system. So there should be some way of registering interrupts in a program so that both the reader and the compiler can clearly tell where they are enabled, and so that state is passed safely between the local scope and the interrupt service routine's scope.

## Error Handling

Error handling isn't the most exciting aspect of a language, but for a language to promote safety and reliability, it needs a good error handling system. I frankly don't know that much about error handling and I'm not planning on doing anything particularly innovative here: the error handling system will likely be modeled after Rust or another modern language.

## Anonymous Functions

With function parameters being immutable by default and the language having no global mutable state, Serene has a decent amount in common with functional programming languages. While Serene is intended to be used in a procedural style, it should at least be possible to mimic a functional style when it suits the problem you are trying to solve.

## Tuning

From the examples here, it might be hard to see how Serene is a *systems* programming language. The base language doesn't expose any control over how data is laid out in memory. While there are no explicit pointers, you can imagine there will be a lot of references and heap allocations involved under-the-hood in creating something like a Region of Vectors, considering both types are dynamically sized. How can a language like this hope to be as fast as C or Rust?

For starters, the language's strict ownership system will allow for aggressive compiler optimization. But for more precise control, there will also be a system of pragmas and annotations for "tuning" your code's performance. While optimizing memory usage in C can involve major structural changes to your code and the potential to reintroduce bugs, the tuning system won't get in the way of business logic. Instead, it will allow you to adjust compiler parameters related to memory and performance for individual functions and types, and it will allow you to set constraints for yourself to "ban" certain operations that are inefficient.

A design principle of the language is that *performance should be orthogonal to correctness*. While manual memory management allows more control over performance, its complexity can lead to bugs. Serene's simple but strict semantics make correctness easy to accomplish, and by allowing independent control of performance parameters, you can experiment with optimizing your code with little risk of breaking it.

## Many Other Things

Serene was intended from the beginning to be a "small language", and I plan on limiting the features to only what is necessary. That said, you could probably make a case that many things I haven't listed here are necessary. Programming languages generally seem to "grow" over time as people demand more features. The initial Serene compiler will likely start out with a very minimalist feature-set, possibly even smaller than what I've shown in the previous sections. And if people start using it, they will almost certainly discover things that aren't possible or ergonomic with the existing features, so the language will need to adapt to address any shortcomings while hopefully keeping its original design intentions intact.