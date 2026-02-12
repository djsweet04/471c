# L2
## Syntax
### Abstract
Assigns the resultant value of a term to an identifier.
### Allocate
Allocate a specified amount of memory.
### Apply
Performs a function (or series of functions), then passes the resultant value to another function.
### Begin
Signifies the start of a function.
### Branch
Create a conditional. Specify the operator, then the terms on the left and right to perform the operation on. If true, navigate to consequent. If not, navigate to otherwise.
### Identifier
Data type that gives names to variables and functions. Acts as an input to most functions.
### Immediate
Simplest data type, consisting solely of integers.
### Let
Assigns an identifier to a term.
### Load
Pull data from allocated memory.
### Primitive
Perform simple math (add, subtract, multiply) with the syntax [operand] [operator1] [operator2].
### Reference
Point to the data/memory location that is bound to an identifier.
### Store
Push information into a specified allocated location of memory.
### Term
A sequence of functions or operations that can be passed to other functions or operations.

## Difference from L3
Letrec has been removed, and no features have been added. This means recursive functions and loops no longer have an abstraction and are done via Let.