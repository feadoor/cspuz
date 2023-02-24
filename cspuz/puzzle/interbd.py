import argparse
import itertools
import sys
import subprocess

import cspuz
from cspuz import Solver, graph, fold_or, count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_interbd(height, width, shapes, numbers):
    solver = Solver()
    division = solver.int_array((height, width), 0, max(max(s) for s in shapes))

    is_black = solver.bool_array((height, width))
    solver.ensure(is_black == (division == 0))
    solver.add_answer_key(is_black)

    for region_idx in range(1, max(max(s) for s in shapes) + 1):
        graph.active_vertices_connected(solver, division[:, :] == region_idx)

    solver.ensure((~is_black).conv2d(2, 1, "and").then(division[:-1, :] == division[1:, :]))
    solver.ensure((~is_black).conv2d(1, 2, "and").then(division[:, :-1] == division[:, 1:]))

    for y in range(height):
        for x in range(width):
            neighbours = [(b, a) for (b, a) in  [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)] if 0 <= b < height and 0 <= a < width]
            solver.ensure(is_black[y, x].then(fold_or([(division[b1, a1] > 0) & (division[b2, a2] > 0) & (division[b1, a1] != division[b2, a2])] for (b1, a1), (b2, a2) in itertools.combinations(neighbours, 2))))

            if shapes[y][x] > 0:
                solver.ensure(division[y, x] == shapes[y][x])

            if numbers[y][x] >= -1:
                if numbers[y][x] > -1:
                    solver.ensure(count_true(is_black.four_neighbors(y, x)) == numbers[y][x])
                solver.ensure(division[y, x] > 0)

    is_sat = solver.solve()
    return is_sat, is_black


def main():
    if len(sys.argv) == 1:
        height = 22
        width = 14
        shapes = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0],
            [2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        numbers = [
            [-2, -2, -1, -2, -2, -2, -2, -2, -2, -2, -1, -2, -2, -2],
            [-2, -1, -2, -2, -2,  2, -2, -2,  1, -2, -2, -1, -2, -2],
            [-1, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -1, -2],
            [-1, -2, -2, -2,  3, -2,  0, -2,  3, -2, -2, -2, -1, -2],
            [-1, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -1, -2],
            [-2, -1, -2, -2, -2,  3, -2,  3, -2, -2, -2, -1, -2, -2],
            [-2, -2, -1, -2,  3, -2,  3, -2,  3, -2, -1, -2, -2, -2],
            [-2, -2, -2,  2, -2,  1, -2,  1, -2,  3, -2,  1, -2, -2],
            [-2,  1, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2],
            [-2, -2, -2,  2, -2, -2,  2, -2, -2,  2, -2, -2,  2, -2],
            [-2,  0, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2],
            [-2, -2, -2,  2, -2,  2, -2,  2, -2,  3, -2,  3, -2, -2],
            [-2, -1, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2],
            [-2, -2, -2, -2,  2, -2,  2, -2, -2, -1, -2, -2, -2, -2],
            [-2,  3, -2,  2, -2,  2, -2, -2,  1, -2,  1, -2,  3, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2, -2,  1, -2, -2, -2, -2],
            [-2, -2, -1, -2,  2, -2, -2,  1, -2, -2,  3, -2, -2, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2],
            [ 2, -2,  2, -2,  3, -2,  1, -2,  2, -2, -2,  1, -2,  2],
            [-2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2],
            [-1, -2, -1, -2,  1, -2, -2, -2, -1, -2, -1, -2, -1, -2],
            [-2, -2, -2, -2, -2, -2,  0, -2, -2, -2, -2, -2, -2, -2],
        ]
        is_sat, is_black = solve_interbd(height, width, shapes, numbers)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", True: "#", False: "."}))
        # for y in range(height):
        #     for x in range(width):
        #         print('.' if numbers[y][x] == -2 else '?' if numbers[y][x] == -1 else numbers[y][x], end=' ')
        #     print()

if __name__ == "__main__":
    main()
