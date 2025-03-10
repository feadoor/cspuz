from cspuz import Solver
from cspuz.array import IntArray2D
from cspuz.constraints import alldifferent, count_true, fold_and, fold_or
from cspuz.puzzle import util

from copy import deepcopy
from itertools import combinations
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

    def add_zipper_line_constraint(self, cells):
        if len(cells) % 2 == 1:
            centre = cells[len(cells) // 2]
            for idx in range(len(cells) // 2):
                self.solver.ensure(self.answer[cells[idx]] + self.answer[cells[-idx-1]] == self.answer[centre])
        else:
            for idx in range(len(cells) // 2):
                for jdx in range(idx + 1, len(cells) // 2):
                    self.solver.ensure(self.answer[cells[idx]] + self.answer[cells[-idx-1]] == self.answer[cells[jdx]] + self.answer[cells[-jdx-1]])

    def add_index_line_constraint(self, cells):
        self.solver.ensure(alldifferent([self.answer[c] for c in cells]))
        for c in cells: self.solver.ensure([self.answer[c] <= len(cells)])
        for p, c in enumerate(cells):
            for v in range(1, len(cells) + 1):
                self.solver.ensure((self.answer[c] == v).then(self.answer[cells[v - 1]] == p + 1))

    def add_black_oebs(self, c1, c2):
        c1_even = (self.answer[c1] == 2) | (self.answer[c1] == 4) | (self.answer[c1] == 6) | (self.answer[c1] == 8)
        c2_even = (self.answer[c2] == 2) | (self.answer[c2] == 4) | (self.answer[c2] == 6) | (self.answer[c2] == 8)
        bigness_differ = ((self.answer[c1] > 5) & (self.answer[c2] < 5)) | ((self.answer[c1] < 5) & (self.answer[c2] > 5))
        parity_differ = (c1_even & (~c2_even)) | ((~c1_even) & c2_even)
        self.solver.ensure(self.answer[c1] != 5)
        self.solver.ensure(self.answer[c2] != 5)
        self.solver.ensure(bigness_differ & parity_differ)

    def add_grey_oebs(self, c1, c2):
        c1_even = (self.answer[c1] == 2) | (self.answer[c1] == 4) | (self.answer[c1] == 6) | (self.answer[c1] == 8)
        c2_even = (self.answer[c2] == 2) | (self.answer[c2] == 4) | (self.answer[c2] == 6) | (self.answer[c2] == 8)
        bigness_differ = ((self.answer[c1] > 5) & (self.answer[c2] < 5)) | ((self.answer[c1] < 5) & (self.answer[c2] > 5))
        parity_differ = (c1_even & (~c2_even)) | ((~c1_even) & c2_even)
        self.solver.ensure(self.answer[c1] != 5)
        self.solver.ensure(self.answer[c2] != 5)
        self.solver.ensure(bigness_differ ^ parity_differ)

    def add_white_oebs(self, c1, c2):
        c1_even = (self.answer[c1] == 2) | (self.answer[c1] == 4) | (self.answer[c1] == 6) | (self.answer[c1] == 8)
        c2_even = (self.answer[c2] == 2) | (self.answer[c2] == 4) | (self.answer[c2] == 6) | (self.answer[c2] == 8)
        bigness_differ = ((self.answer[c1] > 5) & (self.answer[c2] < 5)) | ((self.answer[c1] < 5) & (self.answer[c2] > 5))
        parity_differ = (c1_even & (~c2_even)) | ((~c1_even) & c2_even)
        self.solver.ensure(self.answer[c1] != 5)
        self.solver.ensure(self.answer[c2] != 5)
        self.solver.ensure((~bigness_differ) & (~parity_differ))

    def add_white_ikpork(self, cells):
        for idx in range(len(cells)):
            for jdx in range(idx + 1, len(cells)):
                self.solver.ensure(self.answer[cells[idx]] != self.answer[cells[jdx]] + 1)
                self.solver.ensure(self.answer[cells[jdx]] != self.answer[cells[idx]] + 1)

    def add_black_ikpork(self, cells):
        for idx in range(len(cells)):
            for jdx in range(idx + 1, len(cells)):
                self.solver.ensure(self.answer[cells[idx]] != self.answer[cells[jdx]] + self.answer[cells[jdx]])
                self.solver.ensure(self.answer[cells[jdx]] != self.answer[cells[idx]] + self.answer[cells[idx]])

    def add_counting_circles(self, cells):
        for value in range(1, self.n * self.n + 1):
            none = (count_true(self.answer[c] == value for c in cells) == 0)
            some = (count_true(self.answer[c] == value for c in cells) == value)
            self.solver.ensure(none | some)

    def add_less_than_count(self, cell, cells):
        self.solver.ensure(count_true(self.answer[c] < self.answer[cell] for c in cells) == self.answer[cell])

    def add_shadow_clue(self, cells, value):
        vs = []
        for i in range(1, len(cells)):
            vs.append((self.answer[cells[i]] < self.answer[cells[i - 1]]).cond(self.answer[cells[i]], 0))
        self.solver.ensure(sum(vs) == value)

    def arrow_clauses(self, cell1, cell2):
        pairs = [(1, 2), (3, 4), (4, 5), (6, 7), (7, 8), (8, 9)]
        clauses = []
        for pair in pairs:
            clauses.append((self.answer[cell1] == pair[0]) & (self.answer[cell2] == pair[1]))
        return clauses
    
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
                    if self.answer[y, x].sol is not None and not self.is_determined[-1][y][x]:
                        self.solver.ensure(self.answer[y, x] == self.answer[y, x].sol)
                        self.is_determined[-1][y][x] = True
            return True
        else:
            return False
    
    def is_unique(self):
        return self.solver.has_unique_answer()
    
    def count_answers(self, limit):
        return self.solver.count_answers(limit)

if __name__ == '__main__':

    problem = [
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  1,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    ]

    sudoku = Sudoku()

    clue_cells = []
    clue_values = []

    for y in range(9):
        for x in range(9):
            if problem[y][x] > 0:
                sudoku.add_clue_constraint((y, x), problem[y][x])
            elif problem[y][x] == -1:
                clue_cells.append((y, x))

    sudoku.add_shadow_clue([(1, x) for x in range(9)], 6)
    sudoku.add_shadow_clue([(2, x) for x in range(9)], 5)
    sudoku.add_shadow_clue([(3, x) for x in range(9)], 4)

    sudoku.add_shadow_clue([(y, 1) for y in range(9)], 7)
    sudoku.add_shadow_clue([(y, 2) for y in range(9)], 8)
    sudoku.add_shadow_clue([(y, 3) for y in range(9)], 9)

    sudoku.add_shadow_clue([(5, x) for x in range(8, -1, -1)], 7)
    sudoku.add_shadow_clue([(6, x) for x in range(8, -1, -1)], 6)
    sudoku.add_shadow_clue([(7, x) for x in range(8, -1, -1)], 5)

    sudoku.add_shadow_clue([(y, 5) for y in range(8, -1, -1)], 2)
    sudoku.add_shadow_clue([(y, 6) for y in range(8, -1, -1)], 3)
    sudoku.add_shadow_clue([(y, 7) for y in range(8, -1, -1)], 4)

    def search():
        
        if len(clue_values) == len(clue_cells):
            answer_count = sudoku.count_answers(2)
            if answer_count == 1:
                print(f'UNIQUE: {clue_values}', flush=True)
            else:
                print(f'NON-UNIQUE: {clue_values} ({answer_count} solutions)', file=sys.stderr)

        else:
            for val in range(1, 10):
                # if val in clue_values: continue
                sudoku.push()
                sudoku.add_clue_constraint(clue_cells[len(clue_values)], val)
                if sudoku.solve_irrefutably():
                    clue_values.append(val)
                    search()
                    clue_values.pop()
                sudoku.pop()

    if len(clue_cells) > len(clue_values):
        search()
    else:
        if sudoku.solve_irrefutably():
            print(util.stringify_array(
                sudoku.answer, dict([(None, "?")] + [(i, str(i)) for i in range(1, 10)])
            ))
            print(sudoku.count_answers(1))
        else:
            print("UNSAT")