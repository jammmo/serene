# 4. More Types

In this section, we will learn about several more complex types that are built into Serene.

## Options

Options are used to represent values that may or may not exist. Before making use of the value, the language require you to check that the Option is not None. This is typically done with a `match` statement or an `either` statement, which will both be introduced in the next section of this guide.

## Arrays

An array is a fixed-length sequence elements, where all of the elements are the same type. Indexing an array always returns an Option, because the index used may be outside of the valid range of indexes. If the index is invalid, the indexing operation will return None.

## Vectors

An vector is similar to an array, except its length can be changed after creation. Like an array, indexing a vector returns an Option.