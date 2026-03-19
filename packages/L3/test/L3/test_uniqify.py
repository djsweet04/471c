from L3.syntax import (
    Abstract,
    Apply,
    Immediate,
    Let,
    LetRec,
    Reference,
    Primitive,
    Branch,
    Allocate,
    Load,
    Store,
    Begin,
    Program,
)
from L3.uniqify import Context, uniqify_term, uniqify_program
from util.sequential_name_generator import SequentialNameGenerator


def test_uniqify_term_reference():
    term = Reference(name="x")

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Reference(name="y")

    assert actual == expected


def test_uniqify_immediate():
    term = Immediate(value=42)

    context: Context = dict[str, str]()
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Immediate(value=42)

    assert actual == expected


def test_uniqify_term_let():
    term = Let(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Let(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="y")),
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )

    assert actual == expected


def test_uniqify_term_letrec():
    term = LetRec(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = LetRec(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="y")),
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )

    assert actual == expected


def test_uniqify_term_abstract():
    term = Abstract(
        parameters=["x", "y"],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Abstract(
        parameters=["x0", "y0"],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )

    assert actual == expected


def test_uniqify_term_branch():
    term = Branch(
        operator="==",
        left=Reference(name="x"),
        right=Reference(name="y"),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )

    context: Context = {"x": "y", "y": "z"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Branch(
        operator="==",
        left=Reference(name="y"),
        right=Reference(name="z"),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )

    assert actual == expected


def test_uniqify_term_allocate():
    term = Allocate(count=10)

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Allocate(count=10)

    assert actual == expected


def test_uniqify_term_load():
    term = Load(base=Reference(name="x"), index=0)

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Load(base=Reference(name="y"), index=0)

    assert actual == expected


def test_uniqify_term_store():
    term = Store(base=Reference(name="x"), index=0, value=Immediate(value=42))

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Store(base=Reference(name="y"), index=0, value=Immediate(value=42))

    assert actual == expected


def test_uniqify_term_begin():
    term = Begin(effects=[Reference(name="x")], value=Immediate(value=42))

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Begin(effects=[Reference(name="y")], value=Immediate(value=42))

    assert actual == expected


def test_uniquify_term_primitive():
    term = Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y"))

    context: Context = {"x": "y", "y": "z"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Primitive(operator="+", left=Reference(name="y"), right=Reference(name="z"))

    assert actual == expected


def test_uniquify_term_apply():
    term = Apply(target=Reference(name="f"), arguments=[Reference(name="x"), Reference(name="y")])

    context: Context = {"f": "g", "x": "y", "y": "z"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Apply(target=Reference(name="g"), arguments=[Reference(name="y"), Reference(name="z")])

    assert actual == expected


def test_uniqify_program():
    program = Program(parameters=["x"], body=Reference(name="x"))

    fresh, actual = uniqify_program(program)

    assert actual.parameters == ["x0"]
    assert actual.body == Reference(name="x0")

    # The returned generator should still produce unique names.
    assert fresh("x") != "x"
