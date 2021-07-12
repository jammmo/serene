# Serene

Serene is a minimalist readable systems programming language designed by Jamie Moschella (@jammmo). It is designed to have the same performance and low-overhead memory management as other systems languages, while being simple enough to be learned in a day. It shall also help programmers catch bugs quickly, with strong typing and strict object ownership rules that make behavior explicit and keep the language consistent and easy to understand.

Serene is still being designed, and there is also a compiler in early development: this repo holds both the compiler and the documentation (which can be read in a nicer format [here](https://jamiemoschella.com/serene-ideas/mkdocs/site/)). The compiler is written in Python and Raku, and it translates Serene source code to C++, relying on GCC to compile a standalone executable.
