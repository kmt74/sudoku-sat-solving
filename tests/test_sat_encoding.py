"""Check sequential AMO semantics and SAT Sudoku model construction."""

import itertools
import importlib.util
import unittest

from sudoku_bench.encodings import ENCODINGS
from sudoku_bench.encodings.sequential import at_most_one
from sudoku_bench.models.sat import build_sat_model, cell_variable, decode_sat_model
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.validator import validate_solution


def satisfies(clauses: list[tuple[int, ...]], true_variables: set[int]) -> bool:
    return all(
        any((literal > 0) == (abs(literal) in true_variables) for literal in clause)
        for clause in clauses
    )


def reference_dpll(clauses: list[tuple[int, ...]], assignment: set[int] | None = None) -> set[int] | None:
    """Small test oracle; the production solver is PySAT."""
    assignment = set() if assignment is None else assignment
    while True:
        if not clauses:
            return assignment
        if any(not clause for clause in clauses):
            return None
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is None:
            break
        if -unit in assignment:
            return None
        assignment.add(unit)
        clauses = [tuple(lit for lit in clause if lit != -unit)
                   for clause in clauses if unit not in clause]

    branch_literal = min(clauses, key=len)[0]
    for literal in (branch_literal, -branch_literal):
        reduced = [tuple(lit for lit in clause if lit != -literal)
                   for clause in clauses if literal not in clause]
        model = reference_dpll(reduced, assignment | {literal})
        if model is not None:
            return model
    return None


class SequentialEncodingTests(unittest.TestCase):
    def test_at_most_one_with_all_input_assignments(self) -> None:
        for count in range(0, 5):
            next_id = count + 1

            def new_var() -> int:
                nonlocal next_id
                variable = next_id
                next_id += 1
                return variable

            clauses = at_most_one(list(range(1, count + 1)), new_var)
            auxiliary_ids = range(count + 1, next_id)
            for bits in itertools.product((False, True), repeat=count):
                inputs = {index + 1 for index, bit in enumerate(bits) if bit}
                has_extension = any(
                    satisfies(
                        clauses,
                        inputs | {variable for variable, bit in zip(auxiliary_ids, mask) if bit},
                    )
                    for mask in itertools.product((False, True), repeat=len(auxiliary_ids))
                )
                with self.subTest(count=count, bits=bits):
                    self.assertEqual(has_extension, sum(bits) <= 1)


@unittest.skipUnless(importlib.util.find_spec("pysat"), "install python-sat")
class AllEncodingTests(unittest.TestCase):
    def test_every_encoding_has_exact_amo_projection(self) -> None:
        from pysat.solvers import Solver

        for name, encode in ENCODINGS.items():
            for count in range(0, 7):
                next_id = count + 1

                def new_var() -> int:
                    nonlocal next_id
                    variable = next_id
                    next_id += 1
                    return variable

                clauses = encode(tuple(range(1, count + 1)), new_var)
                with Solver(name="g3", bootstrap_with=clauses) as solver:
                    for bits in itertools.product((False, True), repeat=count):
                        assumptions = [index if bit else -index
                                       for index, bit in enumerate(bits, start=1)]
                        with self.subTest(encoding=name, count=count, bits=bits):
                            self.assertEqual(solver.solve(assumptions=assumptions),
                                             sum(bits) <= 1)


class SatModelTests(unittest.TestCase):
    def test_4x4_model_sizes_and_clue_units(self) -> None:
        puzzle = Puzzle.from_rows([
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [0, 1, 4, 0],
            [4, 0, 0, 1],
        ])
        model = build_sat_model(puzzle)
        self.assertEqual(model.variable_count, 256)
        self.assertEqual(model.clause_count, 584)
        self.assertIn((cell_variable(4, 0, 0, 1),), model.clauses)
        self.assertEqual(max(abs(lit) for clause in model.clauses for lit in clause), 256)

    def test_known_solution_extends_to_a_satisfying_cnf_assignment(self) -> None:
        puzzle = Puzzle.from_rows([
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [0, 1, 4, 0],
            [4, 0, 0, 1],
        ])
        solution = ((1, 2, 3, 4), (3, 4, 1, 2), (2, 1, 4, 3), (4, 3, 2, 1))
        model = build_sat_model(puzzle)
        true_variables = {
            cell_variable(4, row, column, digit)
            for row, values in enumerate(solution)
            for column, digit in enumerate(values)
        }

        next_auxiliary = 4**3 + 1
        for clause in model.clauses:
            if len(clause) == 4:  # An at-least-one group.
                for prefix_end in range(1, 4):
                    if any(literal in true_variables for literal in clause[:prefix_end]):
                        true_variables.add(next_auxiliary)
                    next_auxiliary += 1

        self.assertEqual(next_auxiliary - 1, model.variable_count)
        self.assertTrue(satisfies(list(model.clauses), true_variables))

    def test_decodes_assignment_and_rejects_missing_or_duplicate_cells(self) -> None:
        size = 4
        rows = ((1, 2, 3, 4), (3, 4, 1, 2), (2, 1, 4, 3), (4, 3, 2, 1))
        assignment = [cell_variable(size, row, column, digit)
                      for row, values in enumerate(rows)
                      for column, digit in enumerate(values)]
        self.assertEqual(decode_sat_model(size, assignment), rows)
        with self.assertRaises(ValueError):
            decode_sat_model(size, assignment[:-1])
        with self.assertRaises(ValueError):
            decode_sat_model(size, assignment + [cell_variable(size, 0, 0, 2)])

    def test_reference_sat_solver_finds_4x4_solution_and_proves_unsat(self) -> None:
        solvable = Puzzle.from_rows([
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [0, 1, 4, 0],
            [4, 0, 0, 1],
        ])
        assignment = reference_dpll(list(build_sat_model(solvable).clauses))
        self.assertIsNotNone(assignment)
        solution = decode_sat_model(4, list(assignment))
        self.assertTrue(validate_solution(solvable, solution))

        impossible = Puzzle.from_rows([
            [1, 2, 3, 0],
            [0, 0, 0, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ])
        self.assertIsNone(reference_dpll(list(build_sat_model(impossible).clauses)))


if __name__ == "__main__":
    unittest.main()
