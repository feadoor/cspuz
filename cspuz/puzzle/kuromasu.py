from functools import reduce
import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D

def false_variable(solver):
    v = solver.bool_var()
    solver.ensure(~v)
    return v

def solve_kuromasu(height, width, problem):
    solver = Solver()

    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_not_adjacent(solver, is_black)
    graph.active_vertices_connected(solver, ~is_black)

    def line_length(shaded_cells):
        return reduce(lambda acc, cell: cell.cond(0, 1 + acc), shaded_cells, 0)

    def visible_cells(y, x, is_black):
        visible_up = line_length(is_black[:y, x])
        visible_down = line_length(reversed(is_black[(y + 1):, x]))
        visible_left = line_length(is_black[y, :x])
        visible_right = line_length(reversed(is_black[y, (x + 1):]))
        return visible_up + visible_down + visible_left + visible_right

    for y in range(height):
        for x in range(width):
            if problem[y][x] > 0:
                solver.ensure(~is_black[y, x])
            if problem[y][x] > 1:
                solver.ensure(visible_cells(y, x, is_black) + 1 == problem[y][x])

    is_sat = solver.solve()
    return is_sat, is_black


def generate_kuromasu(
    height, width, disallow_adjacent=False, symmetry=False, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_kuromasu(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(0, 10),
            default=0,
            disallow_adjacent=disallow_adjacent,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=8),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 7
        width = 7
        problem = [
            [ 0,  3,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  2,  0],
            [ 0,  0,  5,  0,  0,  0,  2],
            [ 0,  0,  0, 13,  0,  0,  0],
            [ 8,  0,  0,  0,  5,  0,  0],
            [ 0,  7,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  9,  0],
        ]
        is_sat, is_black = solve_kuromasu(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        for _ in range(10):
            try:
                problem = generate_kuromasu(height, width, disallow_adjacent=False, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, lambda x: "." if x == 0 else 'O' if x == 1 else str(x)), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
