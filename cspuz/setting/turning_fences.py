from cspuz import Solver, graph
from cspuz.array import BoolArray2D
from cspuz.constraints import count_true
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util

from typing import List

import sys

class TurningFences:
    height: int
    width: int
    grid_frame: BoolGridFrame
    is_turn: BoolArray2D
    is_determined: List[List[bool]]
    solver: Solver

    def __init__(self, height, width):
        self.width = width
        self.height = height
        self.solver = Solver()
        self.grid_frame = BoolGridFrame(self.solver, height, width)
        self.is_turn = self.solver.bool_array((height + 1, width + 1))
        self.is_determined = [[False for _ in self.grid_frame.all_edges()]]
        self.add_base_constraints()

    def add_base_constraints(self):
        self.solver.add_answer_key(self.grid_frame)
        graph.active_edges_single_cycle(self.solver, self.grid_frame)
        for y in range(self.height + 1):
            for x in range(self.width + 1):
                vertical_edges = [self.grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < height]
                horizontal_edges = [self.grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < width]
                self.solver.ensure(self.is_turn[y, x] == ((count_true(vertical_edges) == 1) & (count_true(horizontal_edges) == 1)))

    def add_clue_constraint(self, cell, value):
        (y, x) = cell
        vertices = [(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)]
        self.solver.ensure(count_true(self.is_turn[b, a] for b, a in vertices) == value)
    
    def push(self):
        self.solver.push()
        self.is_determined.append(self.is_determined[-1][:])

    def pop(self):
        self.solver.pop()
        self.is_determined.pop()

    def solve_irrefutably(self):
        if self.solver.solve():
            for idx, edge in enumerate(self.grid_frame.all_edges()):
                if edge.sol is not None and not self.is_determined[-1][idx]:
                    self.solver.ensure(edge == edge.sol)
                    self.is_determined[-1][idx] = True
            return True
        else:
            return False
    
    def is_unique(self):
        return self.solver.has_unique_answer()

if __name__ == '__main__':

    problem = [
        [-1,  2,  3, -1,  3,  1, -1,  2,  3, -1],
        [ 3, -1, -1, -1,  1,  1, -1, -1, -1,  3],
        [ 1, -1, -1, -1, -1, -1, -1, -1, -1,  2],
        [-1, -1,  1, -1, -1, -1, -1,  3, -1, -1],
        [ 3, -1, -1,  4, -1, -1,  0, -1, -1,  2],
        [ 1, -1,  4, -1, -1, -1, -1,  1, -1,  1],
        [-1, -1,  3, -1, -1, -1, -1,  1, -1, -1],
        [-1, -1, -1,  0, -1, -1,  4, -1, -1, -1],
        [ 2, -1,  3, -1, -1, -1, -1,  1, -1,  0],
        [-1, -1, -1, -1,  1,  3, -1, -1, -1, -1],
        [-1,  3, -1, -1, -1, -1, -1, -1,  1, -1],
        [ 1, -1,  1, -1, -1, -1, -1,  3, -1,  3],
        [-1,  3, -1, -1,  1,  0, -1, -1,  1, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  0,  2, -1,  2,  2, -1,  2,  0, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  1,  2, -1,  1,  3, -1,  1,  0, -1],
        [-1,  3,  4, -1, -1, -1, -1,  3,  2, -1],
        [-1, -1, -1, -1,  1,  1, -1, -1, -1, -1],
        [ 2, -1, -1,  2, -1, -1,  3, -1, -1,  3],
        [ 1, -1,  3, -1, -1, -1, -1,  2, -1,  1],
        [ 3, -1,  1, -1, -1, -1, -1,  1, -1,  2],
        [ 3, -1, -1,  3, -1, -1,  2, -1, -1,  2],
        [-1, -1, -1, -1,  2,  2, -1, -1, -1, -1],
        [ 3,  2, -1, -1, -1, -1, -1, -1,  3,  3],
        [-1, -1,  1,  2, -1, -1,  2,  1, -1, -1],
        [-1,  3, -1, -1,  1,  2, -1, -1,  1, -1],
        [-1,  2, -1, -1, -1, -1, -1, -1,  2, -1],
        [-1,  3, -1, -1,  0,  0, -1, -1,  1, -1],
        [-1, -1,  1, -1, -1, -1, -1,  2, -1, -1],
        [ 4, -1, -1,  3, -1, -1,  1, -1, -1,  2],
        [ 2, -1, -1, -1,  1,  2, -1, -1, -1,  4],
        [-1,  3,  2, -1, -1, -1, -1,  1,  1, -1],
        [-1, -1, -1, -1,  0,  0, -1, -1, -1, -1],
        [ 1,  2, -1, -1, -1, -1, -1, -1,  3,  2],
        [ 3, -1,  3, -1,  1,  1, -1,  1, -1,  1],
        [-1,  2,  1, -1, -1, -1, -1,  2,  3, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  2,  1, -1,  3,  3, -1,  2,  3, -1],
        [ 3, -1,  3, -1, -1, -1, -1,  1, -1,  1],
        [ 2,  2, -1, -1, -1, -1, -1, -1,  3,  2],
        [-1, -1, -1,  3, -1, -1,  3, -1, -1, -1],
        [ 2, -1,  1, -1,  1,  1, -1,  1, -1,  1],
        [-1,  2, -1,  2, -1, -1,  2, -1,  2, -1],
        [ 3, -1,  3, -1,  3,  3, -1,  3, -1,  1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1,  4, -1,  4, -1, -1,  4, -1,  4, -1],
        [ 2, -1, -1, -1, -1, -1, -1, -1, -1,  3],
        [-1,  4, -1,  4, -1, -1,  4, -1,  4, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [-1, -1,  1, -1,  3,  1, -1,  3, -1, -1],
        [-1,  3, -1, -1, -1, -1, -1, -1,  1, -1],
        [ 4, -1, -1, -1,  0,  0, -1, -1, -1,  0],
        [-1,  1, -1, -1, -1, -1, -1, -1,  3, -1],
        [-1, -1,  3, -1,  1,  3, -1,  1, -1, -1],
        [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [ 2,  2, -1, -1,  3,  2, -1, -1,  2,  1],
        [-1, -1,  2, -1, -1, -1, -1,  2, -1, -1],
        [ 3, -1, -1,  2,  2,  0,  2, -1, -1,  4],
        [-1, -1,  2, -1, -1, -1, -1,  2, -1, -1],
        [ 3,  2, -1, -1, -1, -1, -1, -1,  2,  1],
        [-1, -1, -1, -1,  1,  2, -1, -1, -1, -1],
        [-1, -1, -1,  2, -1, -1,  1, -1, -1, -1],
        [-1, -1,  2, -1, -1, -1, -1,  2, -1, -1],
    ]

    height = len(problem)
    width = len(problem[0])
    assert(all(len(row) == width) for row in problem)

    turning_fences = TurningFences(height, width)
    clue_cells = []
    clue_values = []

    for y in range(height):
        for x in range(width):
            if 0 <= problem[y][x] <= 4:
                turning_fences.add_clue_constraint((y, x), problem[y][x])
            elif problem[y][x] == 5:
                clue_cells.append((y, x))

    def search():

        if len(clue_values) == len(clue_cells):
            print(f'PROGRESS: {clue_values}', file=sys.stderr)
            if turning_fences.is_unique():
                if len(clue_values) == 8:
                    print(f'{clue_values[0]} {clue_values[1]} {clue_values[2]}\n{clue_values[3]}   {clue_values[4]}\n{clue_values[5]} {clue_values[6]} {clue_values[7]}\n', flush=True)
                else:
                    print(f'UNIQUE: {clue_values}', flush=True)

        else:
            for val in range(1, 4):
                turning_fences.push()
                turning_fences.add_clue_constraint(clue_cells[len(clue_values)], val)
                if turning_fences.solve_irrefutably():
                    clue_values.append(val)
                    search()
                    clue_values.pop()
                turning_fences.pop()

    if len(clue_cells) > 0:
        search()
    else:
        turning_fences.solve_irrefutably()
        print(util.stringify_grid_frame(turning_fences.grid_frame))