"""Closure conversion/lifting for L1 to L0 transformation."""

from collections.abc import Sequence

from . import syntax as L1


def _collect_defined_vars(statement: L1.Statement) -> set[str]:
    """Collect all variables defined in a statement."""
    match statement:
        case L1.Copy(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Abstract(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Immediate(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Primitive(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Allocate(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Load(destination=dest, then=then):
            return {dest} | _collect_defined_vars(then)
        case L1.Branch(then=then, otherwise=otherwise):
            return _collect_defined_vars(then) | _collect_defined_vars(otherwise)
        case L1.Store(then=then):
            return _collect_defined_vars(then)
        case L1.Apply() | L1.Halt():  # pragma: no cover
            return set()


def _collect_used_vars(statement: L1.Statement) -> set[str]:
    """Collect all variables used in a statement."""
    match statement:
        case L1.Copy(source=src, then=then):
            return {src} | _collect_used_vars(then)
        case L1.Abstract(parameters=params, body=body, then=then):
            # Variables in the abstract body and then clause
            return (_collect_used_vars(body) | _collect_used_vars(then)) - set(params)
        case L1.Apply(target=tgt, arguments=args):
            return {tgt} | set(args)
        case L1.Immediate(then=then):
            return _collect_used_vars(then)
        case L1.Primitive(left=left, right=right, then=then):
            return {left, right} | _collect_used_vars(then)
        case L1.Branch(left=left, right=right, then=then, otherwise=otherwise):
            return {left, right} | _collect_used_vars(then) | _collect_used_vars(otherwise)
        case L1.Allocate(then=then):
            return _collect_used_vars(then)
        case L1.Load(base=base, then=then):
            return {base} | _collect_used_vars(then)
        case L1.Store(base=base, value=value, then=then):
            return {base, value} | _collect_used_vars(then)
        case L1.Halt(value=value):  # pragma: no cover
            return {value}


def _get_free_vars(statement: L1.Statement, available_vars: set[str]) -> set[str]:
    """Get free variables in a statement given available variables."""
    used = _collect_used_vars(statement)
    defined = _collect_defined_vars(statement)
    # Free variables are those that are used but not available and not defined locally
    return (used - available_vars) - defined


def _convert_statement(
    statement: L1.Statement,
    procedures: list,
    available_vars: set[str],
):
    """Convert an L1 statement to L0, collecting procedures."""
    # Import L0 here to avoid import-time circular dependencies
    import L0.syntax as L0
    
    match statement:
        case L1.Copy(destination=dest, source=src, then=then):
            return L0.Copy(
                destination=dest,
                source=src,
                then=_convert_statement(then, procedures, available_vars | {dest}),
            )

        case L1.Abstract(destination=dest, parameters=params, body=body, then=then):
            # Collect free variables in this closure
            free_vars = sorted(_get_free_vars(body, set(params)))
            
            # Create procedure with free vars as first parameters
            all_params = list(free_vars) + list(params)
            proc_body = _convert_statement(body, procedures, set(params) | set(free_vars))
            
            procedures.append(
                L0.Procedure(
                    name=dest,
                    parameters=all_params,
                    body=proc_body,
                )
            )
            
            # In the L0 code, store the procedure address
            then_stmt = _convert_statement(then, procedures, available_vars | {dest})
            
            # Generate code to store closure values (free variables) if any
            if free_vars:
                # Get the procedure address, allocate closure, and store values
                closure_var = f"_closure_{dest}"
                proc_addr_var = f"_proc_addr_{dest}"
                
                # Get procedure address
                get_addr = L0.Address(
                    destination=proc_addr_var,
                    name=dest,
                    then=L0.Allocate(
                        destination=closure_var,
                        count=1 + len(free_vars),
                        then=_build_closure_stores(proc_addr_var, free_vars, closure_var, then_stmt),
                    ),
                )
                return get_addr
            else:
                # No free variables, just bind the address
                return L0.Address(
                    destination=dest,
                    name=dest,
                    then=then_stmt,
                )

        case L1.Apply(target=tgt, arguments=args):
            # Convert to L0 Call
            return L0.Call(target=tgt, arguments=args)

        case L1.Immediate(destination=dest, value=value, then=then):
            return L0.Immediate(
                destination=dest,
                value=value,
                then=_convert_statement(then, procedures, available_vars | {dest}),
            )

        case L1.Primitive(destination=dest, operator=op, left=left, right=right, then=then):
            return L0.Primitive(
                destination=dest,
                operator=op,
                left=left,
                right=right,
                then=_convert_statement(then, procedures, available_vars | {dest}),
            )

        case L1.Branch(operator=op, left=left, right=right, then=then, otherwise=otherwise):
            return L0.Branch(
                operator=op,
                left=left,
                right=right,
                then=_convert_statement(then, procedures, available_vars),
                otherwise=_convert_statement(otherwise, procedures, available_vars),
            )

        case L1.Allocate(destination=dest, count=count, then=then):
            return L0.Allocate(
                destination=dest,
                count=count,
                then=_convert_statement(then, procedures, available_vars | {dest}),
            )

        case L1.Load(destination=dest, base=base, index=idx, then=then):
            return L0.Load(
                destination=dest,
                base=base,
                index=idx,
                then=_convert_statement(then, procedures, available_vars | {dest}),
            )

        case L1.Store(base=base, index=idx, value=value, then=then):
            return L0.Store(
                base=base,
                index=idx,
                value=value,
                then=_convert_statement(then, procedures, available_vars),
            )

        case L1.Halt(value=value):  # pragma: no cover
            return L0.Halt(value=value)


def _build_closure_stores(
    proc_addr_var: str, free_vars: Sequence[str], closure_var: str, continuation
):
    """Build a sequence of stores to populate a closure."""
    import L0.syntax as L0
    
    # Build stores in forward order: first store procedure address at index 0,
    # then free variables at indices 1, 2, ...
    stmt = continuation
    
    # Build the stores in reverse so that when executed they happen in forward order
    for i, var in enumerate(reversed(free_vars)):
        idx = len(free_vars) - i
        stmt = L0.Store(
            base=closure_var,
            index=idx,
            value=var,
            then=stmt,
        )
    
    # Finally store procedure address at index 0
    stmt = L0.Store(
        base=closure_var,
        index=0,
        value=proc_addr_var,
        then=stmt,
    )
    
    return stmt


def close(program: L1.Program):
    """Convert an L1 program to L0 via closure conversion/lifting."""
    import L0.syntax as L0
    
    procedures: list = []
    
    # Initial available variables are the program parameters
    available_vars = set(program.parameters)
    
    # Convert the body, collecting all procedures
    body = _convert_statement(program.body, procedures, available_vars)
    
    # Create the main procedure
    main_procedure = L0.Procedure(
        name="main",
        parameters=list(program.parameters),
        body=body,
    )
    
    # Return L0 program with main first, then other procedures
    return L0.Program(procedures=[main_procedure, *procedures])
