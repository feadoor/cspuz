import sys
import subprocess

from cspuz import Solver, graph
from cspuz.constraints import count_true, then
from cspuz.puzzle import util

def false_variable(solver):
    v = solver.bool_var()
    solver.ensure(~v)
    return v

def solve_guide_arrow(height, width, clues):

    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)

    graph.active_vertices_not_adjacent(solver, is_black)
    ranks = solver.int_array((height, width), 0, height * width - 1)

    def neighbours(y, x):
        return [(b, a) for (b, a) in [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)] if 0 <= b < height and 0 <= a < width]

    for y in range(height):
        for x in range(width):
            less_ranks = []
            for (b, a) in neighbours(y, x):
                less_ranks.append((ranks[b, a] < ranks[y, x]) & ~is_black[y, x] & ~is_black[b, a])
                if (b, a) < (y, x): solver.ensure(ranks[b, a] != ranks[y, x])
            solver.ensure(then(~is_black[y, x], count_true(less_ranks) == (0 if clues[y][x] == '*' else 1)))

    for y in range(height):
        for x in range(width):
            if clues[y][x] == '*':
                solver.ensure(~is_black[y, x])
            elif clues[y][x] == '<':
                if x == 0: solver.ensure(false_variable(solver))
                else: solver.ensure(~is_black[y, x] & ~is_black[y, x - 1] & (ranks[y, x] > ranks[y, x - 1]))
            elif clues[y][x] == '>':
                if x == width - 1: solver.ensure(false_variable(solver))
                else: solver.ensure(~is_black[y, x] & ~is_black[y, x + 1] & (ranks[y, x] > ranks[y, x + 1]))
            elif clues[y][x] == '^':
                if y == 0: solver.ensure(false_variable(solver))
                else: solver.ensure(~is_black[y, x] & ~is_black[y - 1, x] & (ranks[y, x] > ranks[y - 1, x]))
            elif clues[y][x] == 'v':
                if y == height - 1: solver.ensure(false_variable(solver))
                else: solver.ensure(~is_black[y, x] & ~is_black[y + 1, x] & (ranks[y, x] > ranks[y + 1, x]))

    is_sat = solver.solve()
    return is_sat, is_black

def _main():
    height = 10
    width = 10
    problem = [
        ['.', '.', '.', '.', '.', '.' ,'.' ,'<' ,'.' ,'.'],
        ['.', '.', '.', '.', '.', '.' ,'.' ,'.' ,'.' ,'.'],
        ['.', '^', '.', '.', '>', '.' ,'.' ,'.' ,'.' ,'<'],
        ['.', '.', '.', '.', '.', '.' ,'.' ,'.' ,'.' ,'.'],
        ['.', '.', '.', '.', '.', '.' ,'.' ,'.' ,'.' ,'.'],
        ['.', '.', '.', '<', '.', '.' ,'.' ,'.' ,'.' ,'.'],
        ['.', '.', '.', '.', '.', '>' ,'.' ,'.' ,'.' ,'.'],
        ['.', '.', '*', '.', '.', '.' ,'.' ,'.' ,'.' ,'^'],
        ['.', '.', '.', '.', '.', '.' ,'.' ,'.' ,'.' ,'.'],
        ['.', '.', '.', '.', '.', '.' ,'.' ,'.' ,'.' ,'<'],
    ]
    is_sat, is_black = solve_guide_arrow(height, width, problem)
    print("has answer:", is_sat)
    if is_sat:
        print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))

if __name__ == "__main__":
    _main()
