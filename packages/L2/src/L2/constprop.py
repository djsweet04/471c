from .syntax import (
    Program, Term, Reference, Let, Immediate, Abstract, Apply,
    Primitive, Branch, Allocate, Load, Store, Begin
)

def constant_propagate(program: Program) -> Program:
    """Replace variable references with constant values when possible."""
    body = _propagate_term(program.body, {})
    return program.model_copy(update={"body": body})

def _propagate_term(term: Term, constants: dict[str, int]) -> Term:
    """Recursively propagate constants through a term."""
    match term:
        case Reference(name=name):
            if name in constants:
                return Immediate(value=constants[name])
            return term

        case Let(bindings=bindings, body=body):
            new_constants = constants.copy()
            new_bindings: list[tuple[str, Term]] = []

            for var, value_term in bindings:
                propagated_value = _propagate_term(value_term, new_constants)
                new_bindings.append((var, propagated_value))

                # Track constants only when binding value is immediate
                if isinstance(propagated_value, Immediate):
                    new_constants[var] = propagated_value.value
                else:
                    # Binding shadows any previous constant knowledge
                    new_constants.pop(var, None)

            propagated_body = _propagate_term(body, new_constants)

            # If there are no bindings at all, just return the body
            if not new_bindings:
                return propagated_body

            return Let(bindings=new_bindings, body=propagated_body)

        case Abstract(parameters=params, body=body):
            # Don't propagate across function boundaries
            return Abstract(parameters=params, body=_propagate_term(body, {}))

        case Apply(target=target, arguments=args):
            return Apply(
                target=_propagate_term(target, constants),
                arguments=[_propagate_term(arg, constants) for arg in args],
            )

        case Primitive(operator=op, left=left, right=right):
            return Primitive(
                operator=op,
                left=_propagate_term(left, constants),
                right=_propagate_term(right, constants),
            )

        case Branch(operator=op, left=left, right=right, consequent=cons, otherwise=otherwise):
            return Branch(
                operator=op,
                left=_propagate_term(left, constants),
                right=_propagate_term(right, constants),
                consequent=_propagate_term(cons, constants),
                otherwise=_propagate_term(otherwise, constants),
            )

        case Load(base=base, index=idx):
            return Load(base=_propagate_term(base, constants), index=idx)

        case Store(base=base, index=idx, value=value):
            return Store(
                base=_propagate_term(base, constants),
                index=idx,
                value=_propagate_term(value, constants),
            )

        case Begin(effects=effects, value=value):
            return Begin(
                effects=[_propagate_term(eff, constants) for eff in effects],   #pragma no cover
                value=_propagate_term(value, constants),
            )

        case Immediate() | Allocate():  #pragma no cover
            return term