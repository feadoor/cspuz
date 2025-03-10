from cspuz import Solver
from cspuz.array import BoolArray2D, IntArray2D
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util

from copy import deepcopy
from itertools import combinations
from typing import List

import sys

UP = 1
LEFT = 2
RIGHT = 3
DOWN = 4

class Hinge:
    height: int
    width: int
    shaded: BoolArray2D
    reflect_dir: IntArray2D
    reflect_distance: IntArray2D
    is_determined: List[List[List[bool]]]
    solver: Solver

    def __init__(self, height, width, rooms):
        self.width = width
        self.height = height
        self.solver = Solver()
        self.shaded = self.solver.bool_array((height, width))
        self.reflect_dir = self.solver.int_array((height, width), 0, 4)
        self.reflect_distance = self.solver.int_array((height, width), 0, max(height, width))
        self.is_determined = [[[False for _ in range(width)] for _ in range(height)]]
        self.add_base_constraints(rooms)

    def add_base_constraints(self, rooms):
        self.solver.add_answer_key(self.shaded)
        self.solver.ensure(self.shaded[:, :] ^ (self.reflect_dir[:, :] == 0))
        self.solver.ensure(self.shaded[:, :] ^ (self.reflect_distance[:, :] == 0))

        room_sets = {(y, x) : {(y, x)} for y in range(self.height) for x in range(self.width)}
        for room in rooms:
            for (y1, x1), (y2, x2) in combinations(room, 2):
                room_sets[y1, x1].add((y2, x2))
                room_sets[y2, x2].add((y1, x1))

        # Adjacent shaded cells in the same room must have the same reflection direction
        for y in range(self.height):
            for x in range(self.width):
                if x < self.width - 1 and (y, x + 1) in room_sets[y, x]:
                    self.solver.ensure((self.shaded[y, x] & self.shaded[y, x + 1]).then(self.reflect_dir[y, x] == self.reflect_dir[y, x + 1]))
                if y < self.height - 1 and (y + 1, x) in room_sets[y, x]:
                    self.solver.ensure((self.shaded[y, x] & self.shaded[y + 1, x]).then(self.reflect_dir[y, x] == self.reflect_dir[y + 1, x]))

        # Adjacent shaded cells in different rooms must have opposite reflection directions
        for y in range(self.height):
            for x in range(self.width):
                if x < self.width - 1 and (y, x + 1) not in room_sets[y, x]:
                    self.solver.ensure((self.shaded[y, x] & self.shaded[y, x + 1]).then((self.reflect_dir[y, x] == RIGHT) & (self.reflect_dir[y, x + 1] == LEFT) & (self.reflect_distance[y, x] == 1) & (self.reflect_distance[y, x + 1] == 1)))
                if y < self.height - 1 and (y + 1, x) not in room_sets[y, x]:
                    self.solver.ensure((self.shaded[y, x] & self.shaded[y + 1, x]).then((self.reflect_dir[y, x] == DOWN) & (self.reflect_dir[y + 1, x] == UP) & (self.reflect_distance[y, x] == 1) & (self.reflect_distance[y + 1, x] == 1)))

        # Each connected group must reflect directly over a border
        good_rank = self.solver.int_array((self.height, self.width), 0, max(len(room) for room in rooms))
        self.solver.ensure(((self.reflect_distance[:, :] == 1) | (~self.shaded[:, :])) == (good_rank[:, :] == 0))
        for y in range(self.height):
            for x in range(self.width):
                neighbours = [(b, a) for (b, a) in [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)] if 0 <= b < self.height and 0 <= a < self.width and (b, a) in room_sets]
                self.solver.ensure((good_rank[y, x] > 0).then(fold_or(self.shaded[b, a] & (good_rank[b, a] == good_rank[y, x] - 1) for b, a in neighbours)))

        # Conditions for cells which reflect right
        for y in range(self.height):
            for x in range(self.width):
                if (y, x + 1) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == RIGHT) & (self.reflect_dir[y, x + 1] == RIGHT)).then(self.reflect_distance[y, x] == self.reflect_distance[y, x + 1] + 2))
                if (y + 1, x) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == RIGHT) & (self.reflect_dir[y + 1, x] == RIGHT)).then(self.reflect_distance[y, x] == self.reflect_distance[y + 1, x]))

                self.solver.ensure((self.reflect_dir[y, x] == RIGHT).then(self.reflect_distance[y, x] < self.width - x))
                for d in range(1, self.width - x):
                    self.solver.ensure(((self.reflect_dir[y, x] == RIGHT) & (self.reflect_distance[y, x] == d)).then(self.shaded[y, x + d] & (self.reflect_dir[y, x + d] == LEFT) & (self.reflect_distance[y, x + d] == d)))

        # Conditions for cells which reflect left
        for y in range(self.height):
            for x in range(self.width):
                if (y, x + 1) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == LEFT) & (self.reflect_dir[y, x + 1] == LEFT)).then(self.reflect_distance[y, x] == self.reflect_distance[y, x + 1] - 2))
                if (y + 1, x) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == LEFT) & (self.reflect_dir[y + 1, x] == LEFT)).then(self.reflect_distance[y, x] == self.reflect_distance[y + 1, x]))

                self.solver.ensure((self.reflect_dir[y, x] == LEFT).then(self.reflect_distance[y, x] <= x))
                for d in range(1, x + 1):
                    self.solver.ensure(((self.reflect_dir[y, x] == LEFT) & (self.reflect_distance[y, x] == d)).then(self.shaded[y, x - d] & (self.reflect_dir[y, x - d] == RIGHT) & (self.reflect_distance[y, x - d] == d)))

        # Conditions for cells which reflect down
        for y in range(self.height):
            for x in range(self.width):
                if (y, x + 1) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == DOWN) & (self.reflect_dir[y, x + 1] == DOWN)).then(self.reflect_distance[y, x] == self.reflect_distance[y, x + 1]))
                if (y + 1, x) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == DOWN) & (self.reflect_dir[y + 1, x] == DOWN)).then(self.reflect_distance[y, x] == self.reflect_distance[y + 1, x] + 2))

                self.solver.ensure((self.reflect_dir[y, x] == DOWN).then(self.reflect_distance[y, x] < self.height - y))
                for d in range(1, self.height - y):
                    self.solver.ensure(((self.reflect_dir[y, x] == DOWN) & (self.reflect_distance[y, x] == d)).then(self.shaded[y + d, x] & (self.reflect_dir[y + d, x] == UP) & (self.reflect_distance[y + d, x] == d)))

        # Conditions for cells which reflect up
        for y in range(self.height):
            for x in range(self.width):
                if (y, x + 1) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == UP) & (self.reflect_dir[y, x + 1] == UP)).then(self.reflect_distance[y, x] == self.reflect_distance[y, x + 1]))
                if (y + 1, x) in room_sets[y, x]:
                    self.solver.ensure(((self.reflect_dir[y, x] == UP) & (self.reflect_dir[y + 1, x] == UP)).then(self.reflect_distance[y, x] == self.reflect_distance[y + 1, x] - 2))

                self.solver.ensure((self.reflect_dir[y, x] == UP).then(self.reflect_distance[y, x] <= y))
                for d in range(1, y + 1):
                    self.solver.ensure(((self.reflect_dir[y, x] == UP) & (self.reflect_distance[y, x] == d)).then(self.shaded[y - d, x] & (self.reflect_dir[y - d, x] == DOWN) & (self.reflect_distance[y - d, x] == d)))

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
                    if self.shaded[y, x].sol is not None and not self.is_determined[-1][y][x]:
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

    clues = [10, 4, 3, 4, 3, 2, 3, 2, 3, 2, 2, 4, 1, 1, 3]
    rooms = [
        [(y, x) for y in range(4, 8) for x in range(4, 8)],

        [(y, x) for y in range(2, 4) for x in range(2, 5)],
        [(y, x) for y in range(2, 4) for x in range(5, 8)],
        [(y, x) for y in range(2, 5) for x in range(8, 10)],
        [(y, x) for y in range(5, 8) for x in range(8, 10)],
        [(y, x) for y in range(8, 10) for x in range(7, 10)],
        [(y, x) for y in range(8, 10) for x in range(4, 7)],
        [(y, x) for y in range(7, 10) for x in range(2, 4)],
        [(y, x) for y in range(4, 7) for x in range(2, 4)],

        [(y, x) for y in range(0, 2) for x in range(3, 6)],
        [(y, x) for y in range(0, 2) for x in range(9, 12)],
        [(y, x) for y in range(6, 10) for x in range(10, 12)],
        [(y, x) for y in range(10, 12) for x in range(6, 9)],
        [(y, x) for y in range(10, 12) for x in range(0, 3)],
        [(y, x) for y in range(2, 6) for x in range(0, 2)],

        [(y, x) for y in range(0, 2) for x in range(0, 3)],
        [(y, x) for y in range(0, 2) for x in range(6, 9)],
        [(y, x) for y in range(2, 6) for x in range(10, 12)],
        [(y, x) for y in range(10, 12) for x in range(9, 12)],
        [(y, x) for y in range(10, 12) for x in range(3, 6)],
        [(y, x) for y in range(6, 10) for x in range(0, 2)],
    ]

    clues_to_change = []
    new_clues = []

    hinge = Hinge(height, width, rooms)
    for idx, room in enumerate(rooms):
        if idx < len(clues) and clues[idx] >= 0 and idx not in clues_to_change: hinge.add_clue(room, clues[idx])

    def search():
        if len(new_clues) == len(clues_to_change):
            print(f'PROGRESS: {new_clues}', file=sys.stderr)
            if hinge.is_unique():
                print(f'UNIQUE: {new_clues}', flush=True)

        else:
            for val in list(range(1, len(rooms[clues_to_change[len(new_clues)]]))):
                hinge.push()
                if val >= 0: hinge.add_clue(rooms[clues_to_change[len(new_clues)]], val)
                if hinge.solve_irrefutably():
                    new_clues.append(val)
                    search()
                    new_clues.pop()
                hinge.pop()

    if len(clues_to_change) > 0:
        search()
    elif hinge.solve_irrefutably():
        print(util.stringify_array(hinge.shaded, {None: "?", True: "#", False: "."}))
    else:
        print("UNSAT")
