# 10. Modules

It is extremely helpful to be able to use well-tested existing pieces of code to implement common functionality, or to be able to split your own code into multiple files for organization. Modules allow you to do just that. Like most programming languages, Serene is packaged with a standard library that implements many common functions and datatypes so you don't have to implement them yourself. You can use import statements to control what external modules you want to use. Import statements also allow you to import modules that you have created yourself, by using a relative file path to the module's location.

## Standard Imports

`import Math`

`import AsyncGUI.window as window`

## Local Imports

`import local "lib/MovieReviewTypes.sn"`