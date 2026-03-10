from .syntax import (
    Program,
    Term,
    Reference,
    Let,
    Immediate,
    Abstract,
    Apply,
    Primitive,
    Branch,
    Allocate,
    Load,
    Store,
    Begin,
)


def constant_fold(program: Program) -> Program:
    body = _fold_term(program.body)
    return program.model_copy(update={"body": body})


def _fold_term(term: Term) -> Term:
    match term:
        case Primitive(operator=op, left=left, right=right):
            left_folded = _fold_term(left)
            right_folded = _fold_term(right)

            # If both operands are constants, evaluate
            if isinstance(left_folded, Immediate) and isinstance(right_folded, Immediate):
                result = _evaluate_primitive(op, left_folded.value, right_folded.value)
                return Immediate(value=result)

            return Primitive(operator=op, left=left_folded, right=right_folded)

        case Let(bindings=bindings, body=body):
            folded_bindings = [(var, _fold_term(val)) for var, val in bindings]
            folded_body = _fold_term(body)
            return Let(bindings=folded_bindings, body=folded_body)

        case Abstract(parameters=params, body=body):
            return Abstract(parameters=params, body=_fold_term(body))

        case Apply(target=target, arguments=args):
            return Apply(target=_fold_term(target), arguments=[_fold_term(arg) for arg in args])

        case Branch(operator=op, left=left, right=right, consequent=cons, otherwise=otherwise):
            return Branch(
                operator=op,
                left=_fold_term(left),
                right=_fold_term(right),
                consequent=_fold_term(cons),
                otherwise=_fold_term(otherwise),
            )

        case Load(base=base, index=idx):
            return Load(base=_fold_term(base), index=idx)

        case Store(base=base, index=idx, value=value):
            return Store(base=_fold_term(base), index=idx, value=_fold_term(value))

        case Begin(effects=effects, value=value):
            return Begin(effects=[_fold_term(eff) for eff in effects], value=_fold_term(value))

        case Reference() | Immediate() | Allocate():  # pragma no cover
            return term


def _evaluate_primitive(operator: str, left: int, right: int) -> int:
    match operator:
        case "+":
            return left + right
        case "-":
            return left - right
        case "*":
            return left * right
        case _:
            raise ValueError(f"Unknown operator: {operator}")
