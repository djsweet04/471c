# L1
## Syntax
### Abstract
Assigns the resultant value of a term to an identifier.
### Allocate
Allocate a specified amount of memory.
### Apply
Performs a function (or series of functions), then passes the resultant value to another function.
### Branch
Create a conditional. Specify the operator, then the terms on the left and right to perform the operation on. If true, navigate to consequent. If not, navigate to otherwise.
### Copy
Take a source identifier and copy its value to a destination identifier.
### Halt
Return from a function.
### Identifier
Data type that gives names to variables and functions. Acts as an input to most functions.
### Immediate
Simplest data type, consisting solely of integers.
### Load
Pull data from allocated memory.
### Primitive
Perform simple math (add, subtract, multiply) with the syntax [operand] [operator1] [operator2].
### Statement
A function or operation to be performed.
### Store
Push information into a specified allocated location of memory.

## Differences from L2
Terms have been replaced by Statemenrs, and functions are now made linearly rather than specifying through Let. Each statement now takes another statement as a "then:", providing a continuation of the program from each step. A Halt can be used to stop the program and return. There now also exists the ability to copy values from one identifier to another.