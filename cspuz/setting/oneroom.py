from cspuz import Solver, graph
from cspuz.array import BoolArray2D
from cspuz.constraints import count_true, fold_and
from cspuz.puzzle import util

from copy import deepcopy
from itertools import combinations, product
from typing import List

import sys

class OneRoom:
    height: int
    width: int
    shaded: BoolArray2D
    is_determined: List[List[List[bool]]]
    solver: Solver

    def __init__(self, height, width, rooms):
        self.width = width
        self.height = height
        self.solver = Solver()
        self.shaded = self.solver.bool_array((height, width))
        self.is_determined = [[[False for _ in range(width)] for _ in range(height)]]
        self.add_base_constraints(rooms)

    def add_base_constraints(self, rooms):
        self.solver.add_answer_key(self.shaded)
        graph.active_vertices_not_adjacent(self.solver, self.shaded)
        graph.active_vertices_connected(self.solver, ~self.shaded)

        for room in rooms:
            room_graph = graph.Graph(len(room))
            for (idx, (y1, x1)), (jdx, (y2, x2)) in combinations(enumerate(room), 2):
                if y1 == y2 and (x1 == x2 + 1 or x2 == x1 + 1): room_graph.add_edge(idx, jdx)
                if x1 == x2 and (y1 == y2 + 1 or y2 == y1 + 1): room_graph.add_edge(idx, jdx)
            room_unshaded = [~self.shaded[y, x] for (y, x) in room]
            graph.active_vertices_connected(self.solver, room_unshaded, room_graph)

        for room1, room2 in combinations(rooms, 2):
            pairs = []
            for (y1, x1), (y2, x2) in product(room1, room2):
                if y1 == y2 and (x1 == x2 + 1 or x2 == x1 + 1): pairs.append(((y1, x1), (y2, x2)))
                if x1 == x2 and (y1 == y2 + 1 or y2 == y1 + 1): pairs.append(((y1, x1), (y2, x2)))
            self.solver.ensure(count_true(~self.shaded[y1, x1] & ~self.shaded[y2, x2] for (y1, x1), (y2, x2) in pairs) <= 1)

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

    height = 12
    width = 12

    clues = [6, 4, 2, 3, 1, 4, 2, 2, 2, 2, 0, 3, 2]
    rooms = [
        [(4, 4), (4, 5), (4, 6), (5, 4), (5, 5), (5, 6), (5, 7), (6, 4), (6, 5), (6, 6), (6, 7), (7, 5), (7, 6), (7, 7)],
        [(2, 3), (2, 4), (2, 5), (2, 6), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 2), (4, 3), (5, 2), (5, 3), (6, 2), (6, 3)],
        [(2, 7), (2, 8), (3, 7), (3, 8), (3, 9), (4, 7), (4, 8), (4, 9)],
        [(5, 8), (5, 9), (6, 8), (6, 9), (7, 8), (7, 9), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9), (9, 5), (9, 6), (9, 7), (9, 8)],
        [(7, 2), (7, 3), (7, 4), (8, 2), (8, 3), (8, 4), (9, 3), (9, 4)],

        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1)],
        [(0, 4), (0, 5), (0, 6), (1, 4), (1, 5), (1, 6)],
        [(0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (2, 9), (2, 10), (2, 11), (3, 10), (3, 11), (4, 10), (4, 11)],
        [(5, 10), (5, 11), (6, 10), (6, 11), (7, 10), (7, 11)],
        [(8, 10), (8, 11), (9, 9), (9, 10), (9, 11), (10, 8), (10, 9), (10, 10), (10, 11), (11, 8), (11, 9), (11, 10), (11, 11)],
        [(10, 5), (10, 6), (10, 7), (11, 5), (11, 6), (11, 7)],
        [(7, 0), (7, 1), (8, 0), (8, 1), (9, 0), (9, 1), (9, 2), (10, 0), (10, 1), (10, 2), (10, 3), (10, 4), (11, 0), (11, 1), (11, 2), (11, 3), (11, 4)],
        [(4, 0), (4, 1), (5, 0), (5, 1), (6, 0), (6, 1)],
    ]

    clues_to_change = []
    new_clues = []

    oneroom = OneRoom(height, width, rooms)
    for idx, room in enumerate(rooms):
        if idx < len(clues) and idx not in clues_to_change: oneroom.add_clue(room, clues[idx])

    def search():
        if len(new_clues) == len(clues_to_change):
            print(f'PROGRESS: {new_clues}', file=sys.stderr)
            if oneroom.is_unique():
                print(f'UNIQUE: {new_clues}', flush=True)

        else:
            for val in reversed(range(1, 10)):
                oneroom.push()
                oneroom.add_clue(rooms[clues_to_change[len(new_clues)]], val)
                if oneroom.solve_irrefutably():
                    new_clues.append(val)
                    search()
                    new_clues.pop()
                oneroom.pop()

    if len(clues_to_change) > 0:
        search()
    elif oneroom.solve_irrefutably():
        print(util.stringify_array(oneroom.shaded, {None: "?", True: "#", False: "."}))
    else:
        print("UNSAT")
