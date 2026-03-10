import pytest

from L2.optimize import optimize_program
from L2.fold import constant_fold, _evaluate_primitive
from L2.constprop import constant_propagate
from L2.deadcode import eliminate_dead_code
from L2.syntax import (
    Immediate,
    Primitive,
    Program,
    Let,
    Reference,
    Abstract,
    Apply,
    Branch,
    Allocate,
    Load,
    Store,
    Begin,
)

# =============================================================================
# constant fold
# =============================================================================

def test_fold_constant_and_nonconstant_paths_and_term_walk():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("ptr", Allocate(count=1)),
                ("nc", Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))),
            ],
            body=Begin(
                effects=[
                    Store(
                        base=Primitive(operator="+", left=Immediate(value=10), right=Immediate(value=5)),
                        index=0,
                        value=Primitive(operator="*", left=Immediate(value=2), right=Immediate(value=3)),
                    ),
                    Apply(target=Reference(name="f"), arguments=[]),
                ],
                value=Branch(
                    operator="<",
                    left=Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)),
                    right=Immediate(value=5),
                    consequent=Apply(
                        target=Reference(name="f"),
                        arguments=[Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))],
                    ),
                    otherwise=Begin(
                        effects=[],
                        value=Load(
                            base=Primitive(operator="+", left=Immediate(value=7), right=Immediate(value=8)),
                            index=0,
                        ),
                    ),
                ),
            ),
        ),
    )

    result = constant_fold(program)
    let = result.body
    assert isinstance(let, Let)

    _, nc_val = let.bindings[1]
    assert isinstance(nc_val, Primitive)

    begin = let.body
    assert isinstance(begin, Begin)

    store = begin.effects[0]
    assert store.base == Immediate(value=15)
    assert store.value == Immediate(value=6)

    branch = begin.value
    assert branch.left == Immediate(value=2)

    load = branch.otherwise.value
    assert load.base == Immediate(value=15)


def test_fold_begin_multiple_effects():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)),
                Primitive(operator="+", left=Immediate(value=2), right=Immediate(value=2)),
            ],
            value=Immediate(value=0),
        ),
    )

    result = constant_fold(program)
    begin = result.body
    assert begin.effects[0] == Immediate(value=2)
    assert begin.effects[1] == Immediate(value=4)

def test_fold_unknown_operator_branch():
    with pytest.raises(ValueError):
        _evaluate_primitive("/", 1, 2)

def test_fold_abstract_case_is_visited():
    program = Program(
        parameters=[],
        body=Abstract(
            parameters=["x"],
            body=Primitive(operator="+", left=Immediate(value=2), right=Immediate(value=3)),
        ),
    )
    result = constant_fold(program)
    assert isinstance(result.body, Abstract)
    assert result.body.body == Immediate(value=5)


@pytest.mark.parametrize(
    "term",
    [
        Immediate(value=1),
        Reference(name="x"),
        Allocate(count=2),
    ],
)
def test_fold_top_level_passthrough_variants(term):
    program = Program(parameters=[], body=term)
    result = constant_fold(program)
    assert result.body == term

def test_fold_begin_with_no_effects():
    program = Program(
        parameters=[],
        body=Begin(effects=[], value=Immediate(value=0)),
    )
    result = constant_fold(program)
    assert isinstance(result.body, Begin)
    assert result.body.effects == []


# =============================================================================
# constant propagation
# =============================================================================

def test_constprop_reference_branches_and_loops_and_abstract_boundary():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("a", Immediate(value=10)),          # immediate binding -> tracked
                ("b", Reference(name="y")),          # non-immediate binding -> not tracked
            ],
            body=Branch(
                operator="<",
                left=Primitive(operator="+", left=Reference(name="a"), right=Immediate(value=1)),  # a should propagate
                right=Immediate(value=20),
                consequent=Apply(target=Reference(name="f"), arguments=[]),  # empty args loop
                otherwise=Begin(
                    effects=[],  # empty effects loop
                    value=Abstract(parameters=["z"], body=Reference(name="a")),  # a should NOT propagate inside
                ),
            ),
        ),
    )

    result = constant_propagate(program)
    let = result.body
    assert isinstance(let, Let)

    branch = let.body
    assert isinstance(branch, Branch)

    assert branch.left.left == Immediate(value=10)

    abs_term = branch.otherwise.value
    assert isinstance(abs_term, Abstract)
    assert isinstance(abs_term.body, Reference)


def test_constprop_empty_let_and_allocate_passthrough():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[Allocate(count=3)],
            value=Let(bindings=[], body=Reference(name="x")),
        ),
    )
    result = constant_propagate(program)
    assert result.body.effects[0] == Allocate(count=3)
    assert result.body.value == Reference(name="x")

def test_constprop_top_level_immediate_and_allocate_passthrough():
    p1 = Program(parameters=[], body=Immediate(value=123))
    r1 = constant_propagate(p1)
    assert r1.body == Immediate(value=123)

    p2 = Program(parameters=[], body=Allocate(count=2))
    r2 = constant_propagate(p2)
    assert r2.body == Allocate(count=2)



def test_constprop_shadowing_removes_prior_constant():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Let(
                bindings=[("x", Reference(name="y"))],
                body=Reference(name="x"),
            ),
        ),
    )

    result = constant_propagate(program)

    outer = result.body
    assert isinstance(outer, Let)

    inner = outer.body
    assert isinstance(inner, Let)

    assert inner.body == Reference(name="x")


def test_constprop_begin_multiple_effects():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1)), ("y", Immediate(value=2))],
            body=Begin(
                effects=[Reference(name="x"), Reference(name="y")],
                value=Immediate(value=0),
            ),
        ),
    )

    result = constant_propagate(program)
    begin = result.body.body
    assert begin.effects[0] == Immediate(value=1)
    assert begin.effects[1] == Immediate(value=2)


def test_constprop_begin_with_no_effects():
    program = Program(
        parameters=[],
        body=Begin(effects=[], value=Immediate(value=1)),
    )
    result = constant_propagate(program)
    assert isinstance(result.body, Begin)
    assert result.body.effects == []


def test_constprop_store_load_and_apply_nonempty():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("ptr", Immediate(value=100)),
                ("v", Immediate(value=42)),
            ],
            body=Begin(
                effects=[
                    Store(base=Reference(name="ptr"), index=0, value=Reference(name="v")),
                    Apply(target=Reference(name="f"), arguments=[Reference(name="v")]),
                ],
                value=Load(base=Reference(name="ptr"), index=0),
            ),
        ),
    )

    result = constant_propagate(program)
    let = result.body
    assert isinstance(let, Let)

    begin = let.body
    assert isinstance(begin, Begin)

    store = begin.effects[0]
    assert store.base == Immediate(value=100)
    assert store.value == Immediate(value=42)

    app = begin.effects[1]
    assert app.arguments[0] == Immediate(value=42)

    load = begin.value
    assert load.base == Immediate(value=100)



# =============================================================================
# dead code elimination
# =============================================================================

def test_deadcode_drops_all_bindings_when_unused():
    program = Program(
        parameters=[],
        body=Let(bindings=[("x", Immediate(value=1))], body=Immediate(value=2)),
    )
    result = eliminate_dead_code(program)
    assert result.body == Immediate(value=2)


def test_deadcode_traverses_all_free_vars_cases_and_transitive_needed_vars():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("a", Immediate(value=1)),                 
                ("y", Reference(name="a")),                
                ("ptr", Allocate(count=1)),            
                ("fun", Abstract(                      
                    parameters=["z"],
                    body=Primitive(operator="+", left=Reference(name="z"), right=Reference(name="y")),
                )),
                ("unused", Immediate(value=99)),          
            ],
            body=Begin(
                effects=[
                    Store(base=Reference(name="ptr"), index=0, value=Reference(name="y")),
                    Apply(target=Reference(name="fun"), arguments=[]),               
                    Apply(target=Reference(name="fun"), arguments=[Reference(name="y")]),  
                    Let(bindings=[], body=Reference(name="y")),                       
                    Let(bindings=[("t", Reference(name="y"))], body=Reference(name="t")),  
                    Abstract(parameters=["p"], body=Reference(name="y")),           
                    Begin(effects=[], value=Immediate(value=0)),                 
                ],
                value=Branch(
                    operator="<",
                    left=Primitive(operator="+", left=Reference(name="y"), right=Immediate(value=0)),
                    right=Immediate(value=10),
                    consequent=Load(base=Reference(name="ptr"), index=0),
                    otherwise=Reference(name="y"),
                ),
            ),
        ),
    )

    result = eliminate_dead_code(program)
    assert isinstance(result.body, Let)

    kept = [v for v, _ in result.body.bindings]
    assert "unused" not in kept
    assert set(["a", "y", "ptr", "fun"]).issubset(set(kept))

def test_deadcode_free_vars_multiple_bindings():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("a", Reference(name="x")),
                ("b", Reference(name="y")),
            ],
            body=Reference(name="a"),
        ),
    )

    result = eliminate_dead_code(program)
    assert isinstance(result.body, Let)


@pytest.mark.parametrize(
    "term, expected_type",
    [
        (Reference(name="x"), Reference),
        (Immediate(value=7), Immediate),
        (Allocate(count=1), Allocate),
        (Apply(target=Reference(name="f"), arguments=[]), Apply),
        (Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2)), Primitive),
        (Branch(operator="<", left=Immediate(value=1), right=Immediate(value=2),
                consequent=Immediate(value=1), otherwise=Immediate(value=0)), Branch),
        (Load(base=Reference(name="ptr"), index=0), Load),
        (Store(base=Reference(name="ptr"), index=0, value=Immediate(value=42)), Store),
        (Begin(effects=[], value=Immediate(value=0)), Begin),
        (Abstract(parameters=["x"], body=Reference(name="x")), Abstract),
    ],
)
def test_deadcode_top_level_nonlet_terms(term, expected_type):
    program = Program(parameters=[], body=term)
    result = eliminate_dead_code(program)
    assert isinstance(result.body, expected_type)

def test_deadcode_compute_needed_vars_multiple_iterations():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("a", Reference(name="b")),
                ("b", Reference(name="c")),
                ("c", Immediate(value=1)),
            ],
            body=Reference(name="a"),
        ),
    )

    result = eliminate_dead_code(program)
    kept = [v for v, _ in result.body.bindings]
    assert set(kept) == {"a", "b", "c"}

def test_deadcode_free_vars_empty_bindings():
    program = Program(
        parameters=[],
        body=Let(bindings=[], body=Reference(name="x")),
    )
    result = eliminate_dead_code(program)
    assert isinstance(result.body, Reference)


def test_deadcode_compute_needed_vars_no_iteration():

    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Immediate(value=0),
        ),
    )
    result = eliminate_dead_code(program)
    assert result.body == Immediate(value=0)

def test_deadcode_needed_immediate_does_not_expand_dependencies():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("k", Immediate(value=0))],
            body=Reference(name="k"),
        ),
    )
    result = eliminate_dead_code(program)
    assert isinstance(result.body, Let)
    assert result.body.bindings[0][0] == "k"


# =============================================================================
# optimize program 
# =============================================================================

def test_optimize_breaks_when_no_change():
    program = Program(parameters=[], body=Immediate(value=42))
    assert optimize_program(program) == program


def test_optimize_converges_after_changes():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)))],
            body=Reference(name="x"),
        ),
    )
    result = optimize_program(program)
    assert result.body == Immediate(value=2)

    
def test_fold_minus_branch():
    assert _evaluate_primitive("-", 10, 3) == 7


