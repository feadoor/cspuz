import argparse
import random
import math
import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util
from cspuz.generator import generate_problem, Choice


def solve_galaxy_yajilin(height, width, problem):
    solver = Solver()
    roots = [(y, x) for y in range(height) for x in range(width) if problem[y][x] != '..']
    division = solver.int_array((height, width), 0, len(roots) - 1)
    graph.division_connected(solver, division, len(roots), roots=roots)
    
    for idx, (root_y, root_x) in enumerate(roots):
        solver.ensure(division[root_y, root_x] == idx)
        for y in range(height):
            for x in range(width):
                symm_y, symm_x = (2 * root_y - y, 2 * root_x - x)
                if 0 <= symm_y < height and 0 <= symm_x < width:
                    solver.ensure((division[y, x] == idx) == (division[symm_y, symm_x] == idx))
                else:
                    solver.ensure(division[y, x] != idx)

    for idx, (root_y, root_x) in enumerate(roots):
        direction, value = (problem[root_y][root_x][0], problem[root_y][root_x][1])
        if direction == '^':
            solver.ensure(count_true(division[:root_y, root_x] == idx) == int(value))
        elif direction == 'v':
            solver.ensure(count_true(division[(root_y+1):, root_x] == idx) == int(value))
        elif direction == '<':
            solver.ensure(count_true(division[root_y, :root_x] == idx) == int(value))
        elif direction == '>':
            solver.ensure(count_true(division[root_y, (root_x+1):] == idx) == int(value))

    solver.add_answer_key(division)
    is_sat = solver.solve()
    return is_sat, division


def _main():
    if len(sys.argv) == 1:
        height = 6
        width = 6
        problem = [
            ['..', '..', '<1', '..', '..', '..'],
            ['..', '..', '??', '..', '..', '??'],
            ['..', '..', '??', '..', '..', '..'],
            ['..', '..', '..', '??', '..', '..'],
            ['??', '..', '..', '??', '..', '..'],
            ['..', '..', '..', '>2', '..', '..'],
        ]
        is_sat, ans = solve_galaxy_yajilin(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(ans, lambda x: '{0:3}'.format(x) if x is not None else '  .'))
    else:
        pass


if __name__ == "__main__":
    _main()
