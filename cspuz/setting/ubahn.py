from cspuz import Solver, graph
from cspuz.array import IntArray2D
from cspuz.constraints import count_true
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util

from typing import List

import random
import sys

EMPTY = 0
CROSS = 1
T_JUNCTION = 2
LINE = 3
TURN = 4

class UBahn:
    height: int
    width: int
    grid_frame: BoolGridFrame
    type: IntArray2D
    is_determined: List[List[bool]]
    solver: Solver

    def __init__(self, height, width):
        self.width = width
        self.height = height
        self.solver = Solver()
        self.grid_frame = BoolGridFrame(self.solver, height - 1, width - 1)
        self.type = self.solver.int_array((self.height, self.width), 0, 4)
        self.is_determined = [[False for _ in self.grid_frame.all_edges()]]
        self.add_base_constraints()

    def add_base_constraints(self):
        self.solver.add_answer_key(self.grid_frame)
        for y in range(self.height):
            for x in range(self.width):
                self.solver.ensure(count_true(self.grid_frame.vertex_neighbors(y, x)) != 1)
                self.solver.ensure(self.is_empty((y, x)).then(self.type[y, x] == EMPTY))
                self.solver.ensure(self.is_cross((y, x)).then(self.type[y, x] == CROSS))
                self.solver.ensure(self.is_t_junction((y, x)).then(self.type[y, x] == T_JUNCTION))
                self.solver.ensure(self.is_line((y, x)).then(self.type[y, x] == LINE))
                self.solver.ensure(self.is_turn((y, x)).then(self.type[y, x] == TURN))
        graph.active_edges_connected(self.solver, self.grid_frame)

    def add_row_clue(self, row_idx, type, value):
        self.solver.ensure(count_true(self.type[row_idx, :] == type) == value)

    def add_col_clue(self, col_idx, type, value):
        self.solver.ensure(count_true(self.type[:, col_idx] == type) == value)

    def is_empty(self, cell):
        (y, x) = cell
        return count_true(self.grid_frame.vertex_neighbors(y, x)) == 0

    def is_cross(self, cell):
        (y, x) = cell
        return count_true(self.grid_frame.vertex_neighbors(y, x)) == 4

    def is_t_junction(self, cell):
        (y, x) = cell
        return count_true(self.grid_frame.vertex_neighbors(y, x)) == 3

    def is_line(self, cell):
        (y, x) = cell
        vertical_edges = [self.grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < self.height - 1]
        horizontal_edges = [self.grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < self.width - 1]
        return (
            (count_true(vertical_edges) == 2) & (count_true(horizontal_edges) == 0) |
            (count_true(vertical_edges) == 0) & (count_true(horizontal_edges) == 2)
        )
    
    def is_turn(self, cell):
        (y, x) = cell
        vertical_edges = [self.grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < self.height - 1]
        horizontal_edges = [self.grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < self.width - 1]
        return (count_true(vertical_edges) == 1) & (count_true(horizontal_edges) == 1)
    
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

def fill_random_ubahn(height, width):

    while True:
        ubahn = UBahn(height, width)
        row_clues = [[-1 for _ in range(4)] for _ in range(height)]
        col_clues = [[-1 for _ in range(4)] for _ in range(width)]

        for idx in range(max(height, width)):
            for type in [LINE, TURN, T_JUNCTION, CROSS]:
                if idx < height:
                    row_clue_choices = list(range(0, width + 1))
                    random.shuffle(row_clue_choices)
                    for clue in row_clue_choices:
                        ubahn.push()
                        ubahn.add_row_clue(idx, type, clue)
                        row_clues[idx][type - 1] = clue
                        if ubahn.solve_irrefutably(): break
                        else: ubahn.pop()
                if idx < width:
                    col_clue_choices = list(range(0, height + 1))
                    random.shuffle(col_clue_choices)
                    for clue in col_clue_choices:
                        ubahn.push()
                        ubahn.add_col_clue(idx, type, clue)
                        col_clues[idx][type - 1] = clue
                        if ubahn.solve_irrefutably(): break
                        else: ubahn.pop()

        if ubahn.is_unique():
            ubahn.solve_irrefutably()
            print(util.stringify_grid_frame(ubahn.grid_frame), file=sys.stderr)
            print(row_clues, file=sys.stderr)
            print(col_clues, file=sys.stderr)
            return row_clues, col_clues

def minimise_ubahn(height, width, row_clues, col_clues):
    pass_idx = 0

    while True:
        pass_idx += 1
        clues_to_remove = []

        for idx in range(height):
            for type in [CROSS, T_JUNCTION, LINE, TURN]:
                if row_clues[idx][type - 1] == -1: continue
                ubahn = UBahn(height, width)
                for jdx, clues in enumerate(row_clues):
                    for type_idx, clue in enumerate(clues):
                        if (jdx, type_idx + 1) != (idx, type) and clue != -1:
                            ubahn.add_row_clue(jdx, type_idx + 1, clue)
                for jdx, clues in enumerate(col_clues):
                    for type_idx, clue in enumerate(clues):
                        if clue != -1:
                            ubahn.add_col_clue(jdx, type_idx + 1, clue)
                if ubahn.is_unique():
                    clues_to_remove.append(('ROW', idx, type, row_clues[idx][type - 1]))

        for idx in range(width):
            for type in [CROSS, T_JUNCTION, LINE, TURN]:
                if col_clues[idx][type - 1] == -1: continue
                ubahn = UBahn(height, width)
                for jdx, clues in enumerate(col_clues):
                    for type_idx, clue in enumerate(clues):
                        if (jdx, type_idx + 1) != (idx, type) and clue != -1:
                            ubahn.add_col_clue(jdx, type_idx + 1, clue)
                for jdx, clues in enumerate(row_clues):
                    for type_idx, clue in enumerate(clues):
                        if clue != -1:
                            ubahn.add_row_clue(jdx, type_idx + 1, clue)
                if ubahn.is_unique():
                    clues_to_remove.append(('COL', idx, type, col_clues[idx][type - 1]))

        if len(clues_to_remove) > 0:
            print(f'Found {len(clues_to_remove)} redundant clues on pass {pass_idx}', file=sys.stderr)
            print(clues_to_remove, file=sys.stderr)
            direction, idx, type, value = random.choice(clues_to_remove)
            print(f'Removing {value} from {direction} {idx} {type - 1}', file=sys.stderr)
            if direction == 'ROW': row_clues[idx][type - 1] = -1
            if direction == 'COL': col_clues[idx][type - 1] = -1
        else:
            break

    print(row_clues, file=sys.stderr)
    print(col_clues, file=sys.stderr)

if __name__ == '__main__':

    height = 6
    width = 6

    row_clues, col_clues = fill_random_ubahn(height, width)
    minimise_ubahn(height, width, row_clues, col_clues)

    ubahn = UBahn(len(row_clues), len(col_clues))
    for idx, clues in enumerate(row_clues):
        for type, clue in enumerate(clues):
            if clue != -1:
                ubahn.add_row_clue(idx, type + 1, clue)
    for idx, clues in enumerate(col_clues):
        for type, clue in enumerate(clues):
            if clue != -1:
                ubahn.add_col_clue(idx, type + 1, clue)

    if ubahn.is_unique():
        print("UNIQUE")
        ubahn.solve_irrefutably()
        print(util.stringify_grid_frame(ubahn.grid_frame))
    else:
        print("NON-UNIQUE")
        ubahn.solve_irrefutably()
        print(util.stringify_grid_frame(ubahn.grid_frame))
