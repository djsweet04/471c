from L2 import syntax as L2
from L3 import syntax as L3
from L3.eliminate_letrec import Context, eliminate_letrec_program, eliminate_letrec_term


def test_check_term_let():
    term = L3.Let(
        bindings=[
            ("x", L3.Immediate(value=0)),
        ],
        body=L3.Reference(name="x"),
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[
            ("x", L2.Immediate(value=0)),
        ],
        body=L2.Reference(name="x"),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_eliminate_letrec_program():
    program = L3.Program(
        parameters=[],
        body=L3.Immediate(value=0),
    )

    expected = L2.Program(
        parameters=[],
        body=L2.Immediate(value=0),
    )

    actual = eliminate_letrec_program(program)

    assert actual == expected


def test_eliminate_letrec_term_letrec():
    term = L3.LetRec(
        bindings=[
            ("f", L3.Abstract(parameters=["x"], body=L3.Reference(name="x"))),
        ],
        body=L3.Reference(name="f"),
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[
            (
                "f",
                L2.Abstract(
                    parameters=["x"],
                    body=L2.Reference(name="x"),
                ),
            ),
        ],
        body=L2.Load(base=L2.Reference(name="f"), index=0),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_reference_in_context():
    term = L3.Reference(name="f")
    context: Context = {"f": None}

    expected = L2.Load(base=L2.Reference(name="f"), index=0)
    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_reference_not_in_context():
    term = L3.Reference(name="x")
    context: Context = {}

    expected = L2.Reference(name="x")
    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_abstract():
    term = L3.Abstract(
        parameters=["x", "y"],
        body=L3.Primitive(
            operator="+",
            left=L3.Reference(name="x"),
            right=L3.Reference(name="y"),
        ),
    )

    context: Context = {}

    expected = L2.Abstract(
        parameters=["x", "y"],
        body=L2.Primitive(
            operator="+",
            left=L2.Reference(name="x"),
            right=L2.Reference(name="y"),
        ),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_apply():
    term = L3.Apply(
        target=L3.Reference(name="f"),
        arguments=[L3.Immediate(value=1), L3.Immediate(value=2)],
    )

    context: Context = {}

    expected = L2.Apply(
        target=L2.Reference(name="f"),
        arguments=[L2.Immediate(value=1), L2.Immediate(value=2)],
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_immediate():
    term = L3.Immediate(value=42)
    context: Context = {}

    expected = L2.Immediate(value=42)
    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_primitive():
    term = L3.Primitive(
        operator="+",
        left=L3.Immediate(value=5),
        right=L3.Immediate(value=3),
    )

    context: Context = {}

    expected = L2.Primitive(
        operator="+",
        left=L2.Immediate(value=5),
        right=L2.Immediate(value=3),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_branch():
    term = L3.Branch(
        operator="<",
        left=L3.Immediate(value=5),
        right=L3.Immediate(value=10),
        consequent=L3.Immediate(value=1),
        otherwise=L3.Immediate(value=0),
    )

    context: Context = {}

    expected = L2.Branch(
        operator="<",
        left=L2.Immediate(value=5),
        right=L2.Immediate(value=10),
        consequent=L2.Immediate(value=1),
        otherwise=L2.Immediate(value=0),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_allocate():
    term = L3.Allocate(count=5)
    context: Context = {}

    expected = L2.Allocate(count=5)
    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_load():
    term = L3.Load(
        base=L3.Reference(name="ptr"),
        index=2,
    )

    context: Context = {}

    expected = L2.Load(
        base=L2.Reference(name="ptr"),
        index=2,
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_store():
    term = L3.Store(
        base=L3.Reference(name="ptr"),
        index=1,
        value=L3.Immediate(value=42),
    )

    context: Context = {}

    expected = L2.Store(
        base=L2.Reference(name="ptr"),
        index=1,
        value=L2.Immediate(value=42),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_begin():
    term = L3.Begin(
        effects=[
            L3.Store(
                base=L3.Reference(name="ptr"),
                index=0,
                value=L3.Immediate(value=10),
            ),
        ],
        value=L3.Immediate(value=0),
    )

    context: Context = {}

    expected = L2.Begin(
        effects=[
            L2.Store(
                base=L2.Reference(name="ptr"),
                index=0,
                value=L2.Immediate(value=10),
            ),
        ],
        value=L2.Immediate(value=0),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_nested_letrec_with_reference():
    term = L3.LetRec(
        bindings=[
            (
                "factorial",
                L3.Abstract(
                    parameters=["n"],
                    body=L3.Apply(
                        target=L3.Reference(name="factorial"),
                        arguments=[L3.Reference(name="n")],
                    ),
                ),
            ),
        ],
        body=L3.Apply(
            target=L3.Reference(name="factorial"),
            arguments=[L3.Immediate(value=5)],
        ),
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[
            (
                "factorial",
                L2.Abstract(
                    parameters=["n"],
                    body=L2.Apply(
                        target=L2.Reference(name="factorial"),
                        arguments=[L2.Reference(name="n")],
                    ),
                ),
            ),
        ],
        body=L2.Apply(
            target=L2.Load(base=L2.Reference(name="factorial"), index=0),
            arguments=[L2.Immediate(value=5)],
        ),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected