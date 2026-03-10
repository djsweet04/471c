from .syntax import (
    Program, Term, Reference, Let, Immediate, Abstract, Apply,
    Primitive, Branch, Allocate, Load, Store, Begin
)

def eliminate_dead_code(program: Program) -> Program:
    """Remove bindings of unused variables."""
    body = _eliminate_dead(program.body, set())
    return program.model_copy(update={"body": body})

def _free_vars(term: Term) -> set[str]:
    """Collect all free variable references in a term."""
    match term:
        case Reference(name=name):
            return {name}

        case Let(bindings=bindings, body=body):
            bound_vars = {var for var, _ in bindings}
            free_in_body = _free_vars(body)

            free_in_values: set[str] = set()
            for _, value in bindings:
                free_in_values |= _free_vars(value)

            return (free_in_body | free_in_values) - bound_vars

        case Abstract(parameters=params, body=body):
            return _free_vars(body) - set(params)

        case Apply(target=target, arguments=args):
            free = _free_vars(target)
            for arg in args:
                free |= _free_vars(arg)
            return free

        case Primitive(left=left, right=right):
            return _free_vars(left) | _free_vars(right)

        case Branch(left=left, right=right, consequent=cons, otherwise=otherwise):
            return (
                _free_vars(left)
                | _free_vars(right)
                | _free_vars(cons)
                | _free_vars(otherwise)
            )

        case Load(base=base):
            return _free_vars(base)

        case Store(base=base, value=value):
            return _free_vars(base) | _free_vars(value)

        case Begin(effects=effects, value=value):
            free: set[str] = set()
            for eff in effects:
                free |= _free_vars(eff)
            free |= _free_vars(value)
            return free

        case Immediate() | Allocate():  #pragma no cover
            return set()

def _eliminate_dead(term: Term, live_vars: set[str]) -> Term:
    """Remove dead code from a term."""
    match term:
        case Let(bindings=bindings, body=body):
            needed_vars = _compute_needed_vars(bindings, _free_vars(body))
            new_bindings = [(var, val) for var, val in bindings if var in needed_vars]
            new_body = _eliminate_dead(body, live_vars)
            new_bindings = [(var, _eliminate_dead(val, live_vars)) for var, val in new_bindings]

            if not new_bindings:
                return new_body

            return Let(bindings=new_bindings, body=new_body)

        case Abstract(parameters=params, body=body):
            return Abstract(parameters=params, body=_eliminate_dead(body, set(params)))

        case Apply(target=target, arguments=args):
            return Apply(
                target=_eliminate_dead(target, live_vars),
                arguments=[_eliminate_dead(arg, live_vars) for arg in args],
            )

        case Primitive(operator=op, left=left, right=right):
            return Primitive(
                operator=op,
                left=_eliminate_dead(left, live_vars),
                right=_eliminate_dead(right, live_vars),
            )

        case Branch(operator=op, left=left, right=right, consequent=cons, otherwise=otherwise):
            return Branch(
                operator=op,
                left=_eliminate_dead(left, live_vars),
                right=_eliminate_dead(right, live_vars),
                consequent=_eliminate_dead(cons, live_vars),
                otherwise=_eliminate_dead(otherwise, live_vars),
            )

        case Load(base=base, index=idx):
            return Load(base=_eliminate_dead(base, live_vars), index=idx)

        case Store(base=base, index=idx, value=value):
            return Store(
                base=_eliminate_dead(base, live_vars),
                index=idx,
                value=_eliminate_dead(value, live_vars),
            )

        case Begin(effects=effects, value=value):
            return Begin(
                effects=[_eliminate_dead(eff, live_vars) for eff in effects],
                value=_eliminate_dead(value, live_vars),
            )

        case Reference() | Immediate() | Allocate():    #pragma no cover
            return term

def _compute_needed_vars(
    bindings: list[tuple[str, Term]],
    initially_needed: set[str]
) -> set[str]:
    """Compute needed variables, including transitive dependencies."""
    needed = set(initially_needed)
    changed = True

    while changed: 
        changed = False
        for var, value in bindings:
            if var in needed:
                value_free_vars = _free_vars(value)
                if not value_free_vars.issubset(needed):
                    needed |= value_free_vars
                    changed = True

    return needed