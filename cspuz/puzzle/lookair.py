import itertools
import sys
import subprocess

import cspuz
from cspuz import Solver
from cspuz.constraints import count_true, fold_and, fold_or
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D

def solve_lookair(height, width, problem):
    solver = Solver()

    size = solver.int_array((height + 2, width + 2), 0, min(width, height))
    offset_y = solver.int_array((height + 2, width + 2), 0, min(width, height))
    offset_x = solver.int_array((height + 2, width + 2), 0, min(width, height))
    solver.ensure(offset_x <= size)
    solver.ensure(offset_y <= size)

    is_black = solver.bool_array((height + 2, width + 2))
    solver.ensure(is_black == (size > 0))
    solver.ensure(is_black == (offset_x > 0))
    solver.ensure(is_black == (offset_y > 0))
    solver.add_answer_key(is_black)

    # Dummy cells to avoid edge conditions on the border
    for y in range(height + 2):
        solver.ensure(~is_black[y, 0])
        solver.ensure(~is_black[y, width + 1])
    for x in range(width + 2):
        solver.ensure(~is_black[0, x])
        solver.ensure(~is_black[height + 1, x])

    # Each shaded cell is part of a square
    for y in range(1, height + 1):
        for x in range(1, width + 1):

            solver.ensure((offset_y[y, x] > 1).then((size[y - 1, x] == size[y, x]) & (offset_y[y - 1, x] + 1 == offset_y[y, x])))
            solver.ensure(((size[y, x] > 0) & (offset_y[y, x] < size[y, x])).then((size[y + 1, x] == size[y, x]) & (offset_y[y + 1, x] == offset_y[y, x] + 1)))
            solver.ensure((offset_x[y, x] > 1).then((size[y, x - 1] == size[y, x]) & (offset_x[y, x - 1] + 1 == offset_x[y, x])))
            solver.ensure(((size[y, x] > 0) & (offset_x[y, x] < size[y, x])).then((size[y, x + 1] == size[y, x]) & (offset_x[y, x + 1] == offset_x[y, x] + 1)))

            solver.ensure((offset_y[y, x] == 1).then(size[y - 1, x] == 0))
            solver.ensure(((size[y, x] > 0) & (offset_y[y, x] == size[y, x])).then(size[y + 1, x] == 0))
            solver.ensure((offset_x[y, x] == 1).then(size[y, x - 1] == 0))
            solver.ensure(((size[y, x] > 0) & (offset_x[y, x] == size[y, x])).then(size[y, x + 1] == 0))
    
    # Squares of the same size don't have a direct line of sight
    for y in range(1, height + 1):
        for x0, x1 in itertools.combinations(range(1, width + 1), 2):
            if x1 > x0 + 1:
                solver.ensure(((size[y, x0] > 0) & (size[y, x0] == size[y, x1])).then(fold_or([size[y, x] != 0 for x in range(x0 + 1, x1)])))
    for x in range(1, width + 1):
        for y0, y1 in itertools.combinations(range(1, height + 1), 2):
            if y1 > y0 + 1:
                solver.ensure(((size[y0, x] > 0) & (size[y0, x] == size[y1, x])).then(fold_or([size[y, x] != 0 for y in range(y0 + 1, y1)])))

    # Clues have the appropriate number of shaded cells
    for y in range(1, height + 1):
        for x in range(1, width + 1):
            if problem[y - 1][x - 1] >= 0:
                solver.ensure(count_true([is_black[b, a] for (b, a) in [(y, x), (y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]]) == problem[y - 1][x - 1])

    is_sat = solver.solve()
    return is_sat, is_black[1 : height + 1, 1 : width + 1]


def generate_lookair(
    height, width, disallow_adjacent=False, symmetry=False, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_lookair(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(-1, 6),
            default=-1,
            disallow_adjacent=disallow_adjacent,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=-1, weight=6),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 10
        width = 10
        problem = [
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  3, -1, -1, -1, -1, -1, -1,  5, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1,  4, -1, -1,  1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1,  3, -1, -1,  5, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  5, -1, -1, -1, -1, -1, -1,  4, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        ]
        is_sat, is_black = solve_lookair(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        for _ in range(10):
            try:
                problem = generate_lookair(height, width, disallow_adjacent=False, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, lambda x: "." if x == -1 else str(x)), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
