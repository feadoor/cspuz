from cspuz import Solver, graph
from cspuz.array import BoolArray2D, IntArray2D
from cspuz.constraints import count_true, fold_and
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util

from copy import deepcopy
from typing import List

import sys

class Bramble:
    height: int
    width: int
    shaded: BoolArray2D
    is_determined: List[List[List[bool]]]
    solver: Solver

    def __init__(self, height, width):
        self.width = width
        self.height = height
        self.solver = Solver()
        self.shaded = self.solver.bool_array((height, width))
        self.grid_frame = BoolGridFrame(self.solver, height, width)
        self.is_determined = [[[False for _ in range(width)] for _ in range(height)]]
        self.add_base_constraints()

    def add_base_constraints(self):
        self.solver.add_answer_key(self.shaded)

        g = graph.Graph(self.height * self.width)
        for y in range(0, self.height):
            for x in range(0, self.width):
                if y < self.height - 1: g.add_edge(y * self.width + x, (y + 1) * self.width + x)
                if x < self.width - 1: g.add_edge(y * self.width + x, y * self.width + x + 1)
                if y < self.height - 1 and x < self.width - 1: g.add_edge(y * self.width + x, (y + 1) * self.width + x + 1)
                if y < self.height - 1 and x > 0: g.add_edge(y * self.width + x, (y + 1) * self.width + x - 1)
        graph.active_vertices_connected(self.solver, self.shaded.flatten(), g, acyclic=True)

        size = self.solver.int_array((self.height, self.width), 0, 2)
        self.solver.ensure((size[:, :] == 0) ^ (self.shaded[:, :]))
        for y in range(self.height):
            for x in range(self.width):
                diagonal_neighbours = [size[b, a] for (b, a) in ((y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1)) if 0 <= b < self.height and 0 <= a < self.width]
                adjacent_neighbours = [self.shaded[b, a] for (b, a) in ((y - 1, x), (y, x - 1), (y, x + 1), (y + 1, x)) if 0 <= b < self.height and 0 <= a < self.width]
                self.solver.ensure((size[y, x] == 1).then(fold_and(~x for x in adjacent_neighbours)))
                self.solver.ensure((size[y, x] == 1).then(fold_and(x != 1 for x in diagonal_neighbours)))
                self.solver.ensure((size[y, x] == 2).then(count_true(adjacent_neighbours) == 1))

    def add_room(self, room):
        for (y, x) in room:
            adjacent_neighbours = [self.shaded[b, a] for (b, a) in ((y - 1, x), (y, x - 1), (y, x + 1), (y + 1, x)) if 0 <= b < self.height and 0 <= a < self.width and (b, a) not in room]
            self.solver.ensure(self.shaded[y, x].then(fold_and(~x for x in adjacent_neighbours)))

    def add_clue(self, room, clue):
        self.solver.ensure(count_true(self.shaded[y, x] for (y, x) in room) == clue)
    
    def push(self):
        self.solver.push()
        self.is_determined.append(deepcopy(self.is_determined[-1]))

    def pop(self):
        self.solver.pop()
        self.is_determined.pop()

    def find_solution(self):
        return self.solver.find_answer()

    def solve_irrefutably(self):
        if self.solver.solve():
            for y in range(self.height):
                for x in range(self.width):
                    if self.shaded[y, x].sol is not None:
                        self.solver.ensure(self.shaded[y, x] == self.shaded[y, x].sol)
                        self.is_determined[-1][y][x] = True
            return True
        else:
            return False
    
    def is_unique(self):
        return self.solver.has_unique_answer()

if __name__ == '__main__':

    height = 9
    width = 18

    clues = [
        1, 1, 1, 1, 1, 1, 
        0, 1, 1, 4, 3, 
        3, 1, 2, 5,
        2, 2, 4, 6
    ]
    rooms = [
        [(1, 8), (1, 9)],
        [(7, 8), (7, 9)],
        [(2, 14), (2, 15)],
        [(5, 14), (5, 15)],
        [(3, 2), (3, 3)],        
        [(6, 2), (6, 3)],

        [(y, x) for y in range(0, 7) for x in range(6, 7)],
        [(y, x) for y in range(7, 9) for x in range(6, 7)],
        [(y, x) for y in range(0, 2) for x in range(11, 12)],
        [(y, x) for y in range(2, 9) for x in range(11, 12)],
        [(y, x) for y in range(3, 6) for x in range(7, 11) if (y, x) not in [(4, 8), (4, 9)]],

        [(y, x) for y in range(1, 7) for x in range(12, 13)],
        [(y, x) for y in range(1, 7) for x in range(17, 18)],
        [(y, x) for y in range(0, 1) for x in range(13, 18)],
        [(y, x) for y in range(7, 9) for x in range(12, 18)],

        [(y, x) for y in range(2, 8) for x in range(5, 6)],        
        [(y, x) for y in range(2, 8) for x in range(0, 1)],
        [(y, x) for y in range(8, 9) for x in range(0, 6)],
        [(y, x) for y in range(0, 2) for x in range(0, 6)],

        [(y, x) for y in range(0, 3) for x in range(7, 11) if (y, x) not in [(1, 8), (1, 9)]],
        [(y, x) for y in range(6, 9) for x in range(7, 11) if (y, x) not in [(7, 8), (7, 9)]],
        [(y, x) for y in range(1, 4) for x in range(13, 17) if (y, x) not in [(2, 14), (2, 15)]],
        [(y, x) for y in range(4, 7) for x in range(13, 17) if (y, x) not in [(5, 14), (5, 15)]],
        [(y, x) for y in range(2, 5) for x in range(1, 5) if (y, x) not in [(3, 2), (3, 3)]],
        [(y, x) for y in range(5, 8) for x in range(1, 5) if (y, x) not in [(6, 2), (6, 3)]],
    ]

    clues_to_change = []
    new_clues = []

    bramble = Bramble(height, width)
    for idx, room in enumerate(rooms):
        bramble.add_room(room)
        if idx < len(clues) and idx not in clues_to_change: bramble.add_clue(room, clues[idx])

    def search():
        if len(new_clues) == len(clues_to_change):
            print(f'PROGRESS: {new_clues}', file=sys.stderr)
            if bramble.is_unique():
                print(f'UNIQUE: {new_clues}', flush=True)

        else:
            for val in range(1, 7):
                bramble.push()
                bramble.add_clue(rooms[clues_to_change[len(new_clues)]], val)
                if bramble.solve_irrefutably():
                    new_clues.append(val)
                    search()
                    new_clues.pop()
                bramble.pop()

    if len(clues_to_change) > 0:
        search()
    elif bramble.solve_irrefutably():
        print(util.stringify_array(bramble.shaded, {None: "?", True: "#", False: "."}))
    else:
        print("UNSAT")