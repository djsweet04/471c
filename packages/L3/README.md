# L3
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
Left, right, and children must be valid.
### Identifier
Data type that gives names to variables and functions. Acts as an input to most functions.
### Immediate
Simplest data type, consisting solely of integers.
### Let
Assigns an identifier to a term.
### Letrec
Assigns an identifier to a recurring term.
### Load
Pull data from allocated memory.
### Primitive
Perform simple math (add, subtract, multiply) with the syntax [operator] [left] [right].
Valid if left and right are valid.
### Reference
Point to the data/memory location that is bound to an identifier.
Referenced identifier must be within scope.
### Store
Push information into a specified allocated location of memory.
### Term
A sequence of functions or operations that can be passed to other functions or operations.
