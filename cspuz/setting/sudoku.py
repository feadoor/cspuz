from cspuz import Solver
from cspuz.array import IntArray2D
from cspuz.constraints import alldifferent, count_true, fold_or
from cspuz.puzzle import util

from copy import deepcopy
from typing import List

import sys

class Sudoku:
    n: int
    answer: IntArray2D
    is_determined: List[List[List[bool]]]
    solver: Solver

    def __init__(self, n=3, regions=None):
        self.n = n
        self.solver = Solver()
        self.answer = self.solver.int_array((n * n, n * n), 1, n * n)
        self.is_determined = [[[False for _ in range(n * n)] for _ in range(n * n)]]
        self.add_base_constraints(regions)

    def add_base_constraints(self, regions):
        self.solver.add_answer_key(self.answer)
        for idx in range(self.n * self.n):
            self.solver.ensure(alldifferent(self.answer[idx, :]))
            self.solver.ensure(alldifferent(self.answer[:, idx]))
        if regions is None:
            for y in range(self.n):
                for x in range(self.n):
                    self.solver.ensure(alldifferent(self.answer[y * self.n : (y + 1) * self.n, x * self.n : (x + 1) * self.n]))
        else:
            for region in regions:
                self.solver.ensure(alldifferent(self.answer[y, x] for y, x in region))

    def add_clue_constraint(self, cell, value):
        self.solver.ensure(self.answer[cell] == value)

    def add_pointing_evens_constraint(self, cells, value):
        self.solver.ensure(count_true(fold_or(self.answer[cell] == x for x in range(2, self.n * self.n, 2)) for cell in cells) == value)
    
    def push(self):
        self.solver.push()
        self.is_determined.append(deepcopy(self.is_determined[-1]))

    def pop(self):
        self.solver.pop()
        self.is_determined.pop()

    def solve_irrefutably(self):
        if self.solver.solve():
            for y in range(self.n * self.n):
                for x in range(self.n * self.n):
                    if self.answer[y, x].sol is not None:
                        self.solver.ensure(self.answer[y, x] == self.answer[y, x].sol)
                        self.is_determined[-1][y][x] = True
            return True
        else:
            return False
    
    def is_unique(self):
        return self.solver.has_unique_answer()

if __name__ == '__main__':

    problem = [
        [ 1,  7,  6,  0,  0,  0,  0,  0,  3],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  1,  0,  2,  0,  0,  0],
        [ 0,  0,  3,  0,  0,  0,  5,  0,  0],
        [ 0,  0,  0,  0,  8,  0,  0,  0,  0],
        [ 0,  0,  4,  0,  0,  0,  6,  0,  0],
        [ 0,  0,  0,  7,  0,  9,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 7,  0,  0,  0,  0,  0,  3,  5,  8],
    ]

    sudoku = Sudoku()

    sudoku.add_pointing_evens_constraint([(7, 0), (8, 1)], 1)
    sudoku.add_pointing_evens_constraint([(6, 0), (7, 1), (8, 2)], 2)
    sudoku.add_pointing_evens_constraint([(5, 0), (6, 1), (7, 2), (8, 3)], 3)

    sudoku.add_pointing_evens_constraint([(1, 8), (0, 7)], 1)
    sudoku.add_pointing_evens_constraint([(2, 8), (1, 7), (0, 6)], 2)
    sudoku.add_pointing_evens_constraint([(3, 8), (2, 7), (1, 6), (0, 5)], 3)

    sudoku.add_pointing_evens_constraint([(8, 5), (7, 6), (6, 7), (5, 8)], 3)
    sudoku.add_pointing_evens_constraint([(8, 4), (7, 5), (6, 6), (5, 7), (4, 8)], 4)
    sudoku.add_pointing_evens_constraint([(8, 3), (7, 4), (6, 5), (5, 6), (4, 7), (3, 8)], 4)

    sudoku.add_pointing_evens_constraint([(0, 3), (1, 2), (2, 1), (3, 0)], 2)
    sudoku.add_pointing_evens_constraint([(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)], 3)
    sudoku.add_pointing_evens_constraint([(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)], 3)

    clue_cells = []
    clue_values = []

    for y in range(9):
        for x in range(9):
            if problem[y][x] > 0:
                sudoku.add_clue_constraint((y, x), problem[y][x])
            elif problem[y][x] == -1:
                clue_cells.append((y, x))

    def search():
        
        if len(clue_values) == len(clue_cells):
            print(f'PROGRESS: {clue_values}', file=sys.stderr)
            if sudoku.is_unique():
                print(f'UNIQUE: {clue_values}', flush=True)

        else:
            for val in range(1, 10):
                sudoku.push()
                sudoku.add_clue_constraint(clue_cells[len(clue_values)], val)
                if sudoku.solve_irrefutably():
                    clue_values.append(val)
                    search()
                    clue_values.pop()
                sudoku.pop()

    if len(clue_cells) > 0:
        search()
    else:
        if sudoku.solve_irrefutably():
            print(util.stringify_array(
                sudoku.answer, dict([(None, "?")] + [(i, str(i)) for i in range(1, 10)])
            ))
        else:
            print("UNSAT")