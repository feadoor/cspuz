from functools import reduce
import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D

def solve_canal_view(height, width, problem):
    solver = Solver()

    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_connected(solver, is_black)
    solver.ensure((~is_black).conv2d(2, 2, "or"))

    def line_length(shaded_cells):
        return reduce(lambda acc, cell: cell.cond(1 + acc, 0), shaded_cells, 0)

    def visible_cells(y, x, is_black):
        visible_up = line_length(is_black[:y, x])
        visible_down = line_length(reversed(is_black[(y + 1):, x]))
        visible_left = line_length(is_black[y, :x])
        visible_right = line_length(reversed(is_black[y, (x + 1):]))
        return visible_up + visible_down + visible_left + visible_right

    for y in range(height):
        for x in range(width):
            if problem[y][x] > -2:
                solver.ensure(~is_black[y, x])
            if problem[y][x] >= 0:
                solver.ensure(visible_cells(y, x, is_black) == problem[y][x])

    is_sat = solver.solve()
    return is_sat, is_black


def generate_canal_view(
    height, width, disallow_adjacent=False, symmetry=False, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_canal_view(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(-2, 10),
            default=-2,
            disallow_adjacent=disallow_adjacent,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=-2, weight=6),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 8
        width = 8
        problem = [
            [-2,  5, -2, -2, -2,  2, -2, -2],
            [-2, -2, -2, -2, -2, -2,  6, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2],
            [-2,  3, -2, -2,  4, -2, -2,  3],
            [ 3, -2, -2,  4, -2, -2,  4, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2],
            [-2,  3, -2, -2, -2, -2, -2, -2],
            [-2, -2,  5, -2, -2, -2,  3, -2],
        ]
        is_sat, is_black = solve_canal_view(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        for _ in range(10):
            try:
                problem = generate_canal_view(height, width, disallow_adjacent=False, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, lambda x: "." if x == 0 else 'O' if x == 1 else str(x)), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
