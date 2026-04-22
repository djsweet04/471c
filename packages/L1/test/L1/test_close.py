"""Test cases for L1 closure conversion to L0."""

import pytest
from L1 import syntax as L1, close
from L0 import syntax as L0


class TestCollectDefinedVars:
    """Test _collect_defined_vars helper function."""

    def test_collect_defined_vars_copy(self):
        """Test collecting defined vars from Copy statement."""
        stmt = L1.Copy(destination="x", source="y", then=L1.Halt(value="z"))
        result = close._collect_defined_vars(stmt)
        assert "x" in result

    def test_collect_defined_vars_abstract(self):
        """Test collecting defined vars from Abstract statement."""
        stmt = L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Halt(value="a"),
            then=L1.Halt(value="x"),
        )
        result = close._collect_defined_vars(stmt)
        assert "f" in result

    def test_collect_defined_vars_immediate(self):
        """Test collecting defined vars from Immediate statement."""
        stmt = L1.Immediate(destination="x", value=42, then=L1.Halt(value="x"))
        result = close._collect_defined_vars(stmt)
        assert "x" in result

    def test_collect_defined_vars_primitive(self):
        """Test collecting defined vars from Primitive statement."""
        stmt = L1.Primitive(
            destination="z", operator="+", left="x", right="y", then=L1.Halt(value="z")
        )
        result = close._collect_defined_vars(stmt)
        assert "z" in result

    def test_collect_defined_vars_allocate(self):
        """Test collecting defined vars from Allocate statement."""
        stmt = L1.Allocate(destination="ptr", count=5, then=L1.Halt(value="ptr"))
        result = close._collect_defined_vars(stmt)
        assert "ptr" in result

    def test_collect_defined_vars_load(self):
        """Test collecting defined vars from Load statement."""
        stmt = L1.Load(
            destination="val", base="ptr", index=0, then=L1.Halt(value="val")
        )
        result = close._collect_defined_vars(stmt)
        assert "val" in result

    def test_collect_defined_vars_branch(self):
        """Test collecting defined vars from Branch statement."""
        stmt = L1.Branch(
            operator="<",
            left="x",
            right="y",
            then=L1.Halt(value="x"),
            otherwise=L1.Halt(value="y"),
        )
        result = close._collect_defined_vars(stmt)
        assert len(result) == 0

    def test_collect_defined_vars_store(self):
        """Test collecting defined vars from Store statement."""
        stmt = L1.Store(base="ptr", index=0, value="x", then=L1.Halt(value="x"))
        result = close._collect_defined_vars(stmt)
        assert len(result) == 0

    def test_collect_defined_vars_apply(self):
        """Test collecting defined vars from Apply statement."""
        stmt = L1.Apply(target="f", arguments=["x"])
        result = close._collect_defined_vars(stmt)
        assert len(result) == 0

    def test_collect_defined_vars_halt(self):
        """Test collecting defined vars from Halt statement."""
        stmt = L1.Halt(value="x")
        result = close._collect_defined_vars(stmt)
        assert len(result) == 0

    def test_collect_defined_vars_chain(self):
        """Test collecting defined vars through multiple statements."""
        stmt = L1.Copy(
            destination="a",
            source="b",
            then=L1.Immediate(
                destination="c", value=1, then=L1.Halt(value="c")
            ),
        )
        result = close._collect_defined_vars(stmt)
        assert "a" in result
        assert "c" in result


class TestCollectUsedVars:
    """Test _collect_used_vars helper function."""

    def test_collect_used_vars_copy(self):
        """Test collecting used vars from Copy statement."""
        stmt = L1.Copy(destination="x", source="y", then=L1.Halt(value="x"))
        result = close._collect_used_vars(stmt)
        assert "y" in result
        assert "x" in result

    def test_collect_used_vars_abstract(self):
        """Test collecting used vars from Abstract statement with free vars."""
        stmt = L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Copy(destination="b", source="a", then=L1.Halt(value="x")),
            then=L1.Halt(value="b"),
        )
        result = close._collect_used_vars(stmt)
        # 'a' is a parameter, so it shouldn't be in free vars
        # 'x' and 'b' are used in the abstract and then clause
        assert "x" in result
        assert "b" in result

    def test_collect_used_vars_apply(self):
        """Test collecting used vars from Apply statement."""
        stmt = L1.Apply(target="f", arguments=["a", "b"])
        result = close._collect_used_vars(stmt)
        assert "f" in result
        assert "a" in result
        assert "b" in result

    def test_collect_used_vars_immediate(self):
        """Test collecting used vars from Immediate statement."""
        stmt = L1.Immediate(destination="x", value=42, then=L1.Halt(value="x"))
        result = close._collect_used_vars(stmt)
        assert "x" in result

    def test_collect_used_vars_primitive(self):
        """Test collecting used vars from Primitive statement."""
        stmt = L1.Primitive(
            destination="z", operator="+", left="x", right="y", then=L1.Halt(value="z")
        )
        result = close._collect_used_vars(stmt)
        assert "x" in result
        assert "y" in result
        assert "z" in result

    def test_collect_used_vars_branch(self):
        """Test collecting used vars from Branch statement."""
        stmt = L1.Branch(
            operator="<",
            left="a",
            right="b",
            then=L1.Halt(value="x"),
            otherwise=L1.Halt(value="y"),
        )
        result = close._collect_used_vars(stmt)
        assert "a" in result
        assert "b" in result
        assert "x" in result
        assert "y" in result

    def test_collect_used_vars_allocate(self):
        """Test collecting used vars from Allocate statement."""
        stmt = L1.Allocate(destination="ptr", count=5, then=L1.Halt(value="ptr"))
        result = close._collect_used_vars(stmt)
        assert "ptr" in result

    def test_collect_used_vars_load(self):
        """Test collecting used vars from Load statement."""
        stmt = L1.Load(
            destination="val", base="ptr", index=0, then=L1.Halt(value="val")
        )
        result = close._collect_used_vars(stmt)
        assert "ptr" in result
        assert "val" in result

    def test_collect_used_vars_store(self):
        """Test collecting used vars from Store statement."""
        stmt = L1.Store(base="ptr", index=0, value="x", then=L1.Halt(value="y"))
        result = close._collect_used_vars(stmt)
        assert "ptr" in result
        assert "x" in result
        assert "y" in result

    def test_collect_used_vars_halt(self):
        """Test collecting used vars from Halt statement."""
        stmt = L1.Halt(value="x")
        result = close._collect_used_vars(stmt)
        assert "x" in result


class TestGetFreeVars:
    """Test _get_free_vars helper function."""

    def test_get_free_vars_simple(self):
        """Test identifying free variables."""
        stmt = L1.Copy(destination="y", source="x", then=L1.Halt(value="y"))
        available = {"x", "z"}
        result = close._get_free_vars(stmt, available)
        assert "x" not in result  # x is available
        assert "z" not in result  # z is not used

    def test_get_free_vars_with_free_variables(self):
        """Test identifying free variables that are used but not available."""
        stmt = L1.Primitive(
            destination="z", operator="+", left="x", right="y", then=L1.Halt(value="z")
        )
        available = {"x"}  # y is not available
        result = close._get_free_vars(stmt, available)
        assert "y" in result

    def test_get_free_vars_empty(self):
        """Test when there are no free variables."""
        stmt = L1.Halt(value="x")
        available = {"x"}
        result = close._get_free_vars(stmt, available)
        assert len(result) == 0


class TestConvertStatement:
    """Test _convert_statement function."""

    def test_convert_copy(self):
        """Test converting Copy statement."""
        stmt = L1.Copy(destination="x", source="y", then=L1.Halt(value="x"))
        procedures = []
        result = close._convert_statement(stmt, procedures, {"y"})
        assert isinstance(result, L0.Copy)
        assert result.destination == "x"
        assert result.source == "y"

    def test_convert_immediate(self):
        """Test converting Immediate statement."""
        stmt = L1.Immediate(destination="x", value=42, then=L1.Halt(value="x"))
        procedures = []
        result = close._convert_statement(stmt, procedures, set())
        assert isinstance(result, L0.Immediate)
        assert result.destination == "x"
        assert result.value == 42

    def test_convert_primitive(self):
        """Test converting Primitive statement."""
        stmt = L1.Primitive(
            destination="z", operator="+", left="x", right="y", then=L1.Halt(value="z")
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, {"x", "y"})
        assert isinstance(result, L0.Primitive)
        assert result.destination == "z"
        assert result.operator == "+"

    def test_convert_branch(self):
        """Test converting Branch statement."""
        stmt = L1.Branch(
            operator="<",
            left="x",
            right="y",
            then=L1.Halt(value="x"),
            otherwise=L1.Halt(value="y"),
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, {"x", "y"})
        assert isinstance(result, L0.Branch)
        assert result.operator == "<"

    def test_convert_allocate(self):
        """Test converting Allocate statement."""
        stmt = L1.Allocate(destination="ptr", count=5, then=L1.Halt(value="ptr"))
        procedures = []
        result = close._convert_statement(stmt, procedures, set())
        assert isinstance(result, L0.Allocate)
        assert result.destination == "ptr"
        assert result.count == 5

    def test_convert_load(self):
        """Test converting Load statement."""
        stmt = L1.Load(
            destination="val", base="ptr", index=2, then=L1.Halt(value="val")
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, {"ptr"})
        assert isinstance(result, L0.Load)
        assert result.destination == "val"
        assert result.base == "ptr"
        assert result.index == 2

    def test_convert_store(self):
        """Test converting Store statement."""
        stmt = L1.Store(base="ptr", index=1, value="x", then=L1.Halt(value="x"))
        procedures = []
        result = close._convert_statement(stmt, procedures, {"ptr", "x"})
        assert isinstance(result, L0.Store)
        assert result.base == "ptr"
        assert result.index == 1
        assert result.value == "x"

    def test_convert_apply(self):
        """Test converting Apply statement."""
        stmt = L1.Apply(target="f", arguments=["x", "y"])
        procedures = []
        result = close._convert_statement(stmt, procedures, {"f", "x", "y"})
        assert isinstance(result, L0.Call)
        assert result.target == "f"
        assert list(result.arguments) == ["x", "y"]

    def test_convert_halt(self):
        """Test converting Halt statement."""
        stmt = L1.Halt(value="x")
        procedures = []
        result = close._convert_statement(stmt, procedures, {"x"})
        assert isinstance(result, L0.Halt)
        assert result.value == "x"

    def test_convert_abstract_no_free_vars(self):
        """Test converting Abstract statement with no free variables."""
        stmt = L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Halt(value="a"),
            then=L1.Halt(value="f"),
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, set())
        assert isinstance(result, L0.Address)
        assert result.destination == "f"
        assert result.name == "f"
        assert len(procedures) == 1
        assert procedures[0].name == "f"
        assert procedures[0].parameters == ["a"]

    def test_convert_abstract_with_free_vars(self):
        """Test converting Abstract statement with free variables."""
        stmt = L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Primitive(
                destination="b",
                operator="+",
                left="a",
                right="x",
                then=L1.Halt(value="b"),
            ),
            then=L1.Halt(value="f"),
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, {"x"})
        assert isinstance(result, L0.Address)
        # Check that procedure was created with free vars
        assert len(procedures) == 1
        proc = procedures[0]
        assert proc.name == "f"
        # Parameters should include free var 'x' first, then parameter 'a'
        assert "x" in proc.parameters
        assert "a" in proc.parameters

    def test_convert_abstract_with_multiple_free_vars(self):
        """Test converting Abstract with multiple free variables."""
        stmt = L1.Abstract(
            destination="f",
            parameters=["a"],
            body=L1.Primitive(
                destination="b",
                operator="+",
                left="x",
                right="y",
                then=L1.Halt(value="b"),
            ),
            then=L1.Halt(value="f"),
        )
        procedures = []
        result = close._convert_statement(stmt, procedures, {"x", "y"})
        assert len(procedures) == 1
        proc = procedures[0]
        # All three should be in parameters
        assert "x" in proc.parameters
        assert "y" in proc.parameters
        assert "a" in proc.parameters


class TestBuildClosureStores:
    """Test _build_closure_stores helper function."""

    def test_build_closure_stores_single_free_var(self):
        """Test building closure with one free variable."""
        continuation = L0.Halt(value="result")
        result = close._build_closure_stores("proc_addr", ["x"], "closure", continuation)
        # Should have stores for the procedure address and free var
        assert isinstance(result, L0.Store)
        # First store should be at index 0 (procedure address)
        assert result.index == 0
        assert result.value == "proc_addr"

    def test_build_closure_stores_multiple_free_vars(self):
        """Test building closure with multiple free variables."""
        continuation = L0.Halt(value="result")
        result = close._build_closure_stores(
            "proc_addr", ["x", "y", "z"], "closure", continuation
        )
        # Should build nested stores
        assert isinstance(result, L0.Store)
        # First store should be at index 0 (procedure address)
        assert result.index == 0


class TestClose:
    """Test the main close function."""

    def test_close_simple_program(self):
        """Test closing a simple program without closures."""
        program = L1.Program(
            parameters=["x"],
            body=L1.Copy(destination="y", source="x", then=L1.Halt(value="y")),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1
        # Main procedure should be first
        assert result.procedures[0].name == "main"
        assert list(result.procedures[0].parameters) == ["x"]

    def test_close_program_with_immediate(self):
        """Test closing a program with Immediate statement."""
        program = L1.Program(
            parameters=[],
            body=L1.Immediate(
                destination="x", value=42, then=L1.Halt(value="x")
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1

    def test_close_program_with_primitive(self):
        """Test closing a program with Primitive operation."""
        program = L1.Program(
            parameters=["x", "y"],
            body=L1.Primitive(
                destination="z", operator="+", left="x", right="y", then=L1.Halt(value="z")
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1
        assert result.procedures[0].name == "main"
        assert set(result.procedures[0].parameters) == {"x", "y"}

    def test_close_program_with_branch(self):
        """Test closing a program with Branch statement."""
        program = L1.Program(
            parameters=["x", "y"],
            body=L1.Branch(
                operator="<",
                left="x",
                right="y",
                then=L1.Halt(value="x"),
                otherwise=L1.Halt(value="y"),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1

    def test_close_program_with_closure_no_free_vars(self):
        """Test closing a program with a closure that has no free variables."""
        program = L1.Program(
            parameters=[],
            body=L1.Abstract(
                destination="f",
                parameters=["a"],
                body=L1.Halt(value="a"),
                then=L1.Halt(value="f"),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        # Should have main and f procedures
        assert len(result.procedures) >= 2
        assert result.procedures[0].name == "main"
        procedure_names = [p.name for p in result.procedures]
        assert "f" in procedure_names

    def test_close_program_with_closure_free_vars(self):
        """Test closing a program with a closure that has free variables."""
        program = L1.Program(
            parameters=["x"],
            body=L1.Abstract(
                destination="f",
                parameters=["a"],
                body=L1.Primitive(
                    destination="b",
                    operator="+",
                    left="x",
                    right="a",
                    then=L1.Halt(value="b"),
                ),
                then=L1.Halt(value="f"),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        # Should have main and f procedures
        assert len(result.procedures) >= 2
        assert result.procedures[0].name == "main"

    def test_close_program_with_allocate_and_load(self):
        """Test closing a program with memory operations."""
        program = L1.Program(
            parameters=[],
            body=L1.Allocate(
                destination="ptr",
                count=10,
                then=L1.Load(
                    destination="val",
                    base="ptr",
                    index=0,
                    then=L1.Halt(value="val"),
                ),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1

    def test_close_program_with_store(self):
        """Test closing a program with Store statement."""
        program = L1.Program(
            parameters=[],
            body=L1.Allocate(
                destination="ptr",
                count=10,
                then=L1.Immediate(
                    destination="val",
                    value=42,
                    then=L1.Store(
                        base="ptr", index=0, value="val", then=L1.Halt(value="val")
                    ),
                ),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert len(result.procedures) >= 1

    def test_close_program_nested_closures(self):
        """Test closing a program with nested closures."""
        inner_abstract = L1.Abstract(
            destination="inner",
            parameters=["y"],
            body=L1.Halt(value="y"),
            then=L1.Halt(value="inner"),
        )
        program = L1.Program(
            parameters=[],
            body=L1.Abstract(
                destination="outer",
                parameters=["a"],
                body=inner_abstract,
                then=L1.Halt(value="outer"),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        # Should have main and two procedure definitions
        assert len(result.procedures) >= 2

    def test_close_program_complex_flow(self):
        """Test closing a more complex program with multiple statement types."""
        program = L1.Program(
            parameters=["start"],
            body=L1.Copy(
                destination="x",
                source="start",
                then=L1.Primitive(
                    destination="y",
                    operator="+",
                    left="x",
                    right="x",
                    then=L1.Allocate(
                        destination="ptr",
                        count=1,
                        then=L1.Store(
                            base="ptr",
                            index=0,
                            value="y",
                            then=L1.Load(
                                destination="result",
                                base="ptr",
                                index=0,
                                then=L1.Halt(value="result"),
                            ),
                        ),
                    ),
                ),
            ),
        )
        result = close.close(program)
        assert isinstance(result, L0.Program)
        assert result.procedures[0].name == "main"
