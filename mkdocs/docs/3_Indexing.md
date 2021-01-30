# Example: Indexing

Here is an example of using the indexing operator on a `Handle`. To deal with the `Option` type that is returned, we use the `either` construct. `either` will try to execute the statement in parentheses, and if any part of it returns `None`, then it will stop executing that statement (in this case, it would stop without mutating `currentObject`) and it would instead execute the second statement, after the keyword `or`.

```
// Assume that the LinkedList struct redirects its subscripting to LinkedList.objects

function findTail(L: LinkedList) -> Handle {
    either (var currentObject = L[L.head]) or return None
    while (True) {
        var currentIndex = currentObject.next
        either (set currentObject = L[currentIndex]) or return currentIndex
    }
}


function removeTail(mutate L: LinkedList) {
    either (var currentObject = L[L.head]) or return
    while (True) {
        var currentIndex = currentObject.next
        either (set currentObject = L[currentIndex]) or break
    }
    run L.delete!(currentIndex)
}

// Error: what happens to currentObject after L.delete!(currentIndex) ?
```

