from .syntax import Program
from .constprop import constant_propagate
from .deadcode import eliminate_dead_code
from .fold import constant_fold


def optimize_program(program: Program) -> Program:
    """Optimize a program by repeatedly applying optimization passes until convergence."""
    while True:
        optimized = program
        optimized = constant_fold(optimized)
        optimized = constant_propagate(optimized)
        optimized = eliminate_dead_code(optimized)
        
        # If no changes were made, we've reached a fixed point
        if optimized == program:
            break
        
        program = optimized
    
    return program
