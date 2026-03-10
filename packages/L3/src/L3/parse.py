from collections.abc import Sequence
from pathlib import Path

from lark import Lark, Token, Transformer
from lark.visitors import v_args  # pyright: ignore[reportUnknownVariableType]

from .syntax import (
    Identifier,
    Let,
    LetRec,
    Reference,
    Abstract,
    Apply,
    Program,
    Term,
    Immediate,
    Branch,
    Primitive,
    Allocate,
    Load,
    Store,
    Begin,
)


class AstTransformer(Transformer[Token, Program | Term]):
    @v_args(inline=True)
    def program(
        self,
        _program: Token,
        parameters: Sequence[Identifier],
        body: Term,
    ) -> Program:
        return Program(
            parameters=parameters,
            body=body,
        )

    def parameters(
        self,
        parameters: Sequence[Token],
    ) -> Sequence[Identifier]:
        return [p.value for p in parameters]

    @v_args(inline=True)
    def term(
        self,
        term: Term,
    ) -> Term:
        return term

    @v_args(inline=True)
    def let(
        self,
        _let: Token,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return Let(
            bindings=bindings,
            body=body,
        )

    @v_args(inline=True)
    def letrec(
        self,
        _letrec: Token,
        bindings: Sequence[tuple[Identifier, Term]],
        body: Term,
    ) -> Term:
        return LetRec(
            bindings=bindings,
            body=body,
        )

    def bindings(
        self,
        bindings: Sequence[tuple[Identifier, Term]],
    ) -> Sequence[tuple[Identifier, Term]]:
        return bindings

    @v_args(inline=True)
    def binding(
        self,
        name: Token,
        value: Term,
    ) -> tuple[Identifier, Term]:
        return name.value, value

    @v_args(inline=True)
    def reference(
        self,
        name: Token,
    ) -> Term:
        return Reference(name=name.value)

    @v_args(inline=True)
    def immediate(
        self,
        value: Token,
    ) -> Term:
        return Immediate(value=int(value.value))

    @v_args(inline=True)
    def abstract(
        self,
        _lambda: Token,
        parameters: Sequence[Identifier],
        body: Term,
    ) -> Term:
        return Abstract(
            parameters=parameters,
            body=body,
        )

    @v_args(inline=True)
    def apply(
        self,
        target: Term,
        *arguments: Term,
    ) -> Term:
        return Apply(
            target=target,
            arguments=list(arguments),
        )

    @v_args(inline=True)
    def primitive(
        self,
        operator: Token,
        left: Term,
        right: Term,
    ) -> Term:
        return Primitive(
            operator=operator.value,
            left=left,
            right=right,
        )

    @v_args(inline=True)
    def branch(
        self,
        _if: Token,
        operator: Token,
        left: Term,
        right: Term,
        consequent: Term,
        otherwise: Term,
    ) -> Term:
        return Branch(
            operator=operator.value,
            left=left,
            right=right,
            consequent=consequent,
            otherwise=otherwise,
        )

    @v_args(inline=True)
    def allocate(
        self,
        _allocate: Token,
        count: Term,
    ) -> Term:
        if isinstance(count, Immediate):
            return Allocate(count=count.value)
        else:
            raise ValueError(f"Allocate count must be an immediate value, got {count}")

    @v_args(inline=True)
    def load(
        self,
        _load: Token,
        base: Term,
        index: Term,
    ) -> Term:
        if isinstance(index, Immediate):
            return Load(base=base, index=index.value)
        else:
            raise ValueError(f"Load index must be an immediate value, got {index}")

    @v_args(inline=True)
    def store(
        self,
        _store: Token,
        base: Term,
        index: Term,
        value: Term,
    ) -> Term:
        if isinstance(index, Immediate):
            return Store(base=base, index=index.value, value=value)
        else:
            raise ValueError(f"Store index must be an immediate value, got {index}")

    @v_args(inline=True)
    def begin(
        self,
        _begin: Token,
        *terms: Term,
    ) -> Term:
        if not terms:
            raise ValueError("Begin must have at least one term")
        return Begin(
            effects=list(terms[:-1]),
            value=terms[-1],
        )


def parse_term(source: str) -> Term:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, start="term", parser="lalr")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]


def parse_program(source: str) -> Program:
    grammar = Path(__file__).with_name("L3.lark").read_text()
    parser = Lark(grammar, start="program", parser="lalr")
    tree = parser.parse(source)  # pyright: ignore[reportUnknownMemberType]
    return AstTransformer().transform(tree)  # pyright: ignore[reportReturnType]
