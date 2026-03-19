from collections.abc import Callable, Mapping
from functools import partial

from util.sequential_name_generator import SequentialNameGenerator

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
)

type Context = Mapping[str, str]


def uniqify_term(
    term: Term,
    context: Context,
    fresh: Callable[[str], str],
) -> Term:
    # Bind only the generator so recursive calls can pass a different context.
    _term = partial(uniqify_term, fresh=fresh)

    match term:
        case Let(bindings=bindings, body=body):
            local = {name: fresh(name) for name, _ in bindings}
            return Let(
                # Binding expressions are evaluated in the outer context.
                bindings=[(local[name], _term(value, context)) for name, value in bindings],
                body=_term(body, {**context, **local}),
            )

        case LetRec(bindings=bindings, body=body):
            local = {name: fresh(name) for name, _ in bindings}
            return LetRec(
                # Each binding can refer to its own renamed name (for recursion),
                # but other bindings should not affect its right-hand side.
                bindings=[(local[name], _term(value, {**context, name: local[name]})) for name, value in bindings],
                body=_term(body, {**context, **local}),
            )

        case Reference(name=name):
            return Reference(name=context[name])

        case Abstract(parameters=parameters, body=body):
            local = {parameter: fresh(parameter) for parameter in parameters}
            return Abstract(
                parameters=[local[parameter] for parameter in parameters],
                body=_term(body, {**context, **local}),
            )

        case Apply(target=target, arguments=arguments):
            return Apply(
                target=_term(target, context),
                arguments=[_term(arg, context) for arg in arguments],
            )

        case Immediate(value=value):
            return Immediate(value=value)

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(
                operator=operator,
                left=_term(left, context),
                right=_term(right, context),
            )

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=_term(left, context),
                right=_term(right, context),
                consequent=_term(consequent, context),
                otherwise=_term(otherwise, context),
            )

        case Allocate(count=count):
            return Allocate(count=count)

        case Load(base=base, index=index):
            return Load(base=_term(base, context), index=index)

        case Store(base=base, index=index, value=value):
            return Store(
                base=_term(base, context),
                index=index,
                value=_term(value, context),
            )

        case Begin(effects=effects, value=value):  # pragma: no branch
            return Begin(
                effects=[_term(effect, context) for effect in effects],
                value=_term(value, context),
            )


def uniqify_program(
    program: Program,
) -> tuple[Callable[[str], str], Program]:
    fresh = SequentialNameGenerator()

    _term = partial(uniqify_term, fresh=fresh)

    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            local = {parameter: fresh(parameter) for parameter in parameters}
            return (
                fresh,
                Program(
                    parameters=[local[parameter] for parameter in parameters],
                    body=_term(body, local),
                ),
            )
