import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_kurotto(height, width, problem):
    solver = Solver()

    is_black = solver.bool_array((height, width))
    size = solver.int_array((height, width), 1, height * width)
    solver.add_answer_key(is_black)

    for y in range(height):
        for x in range(width):
            if problem[y][x] > -2:
                solver.ensure(~is_black[y, x])

    group_id = graph.division_connected_variable_groups(solver, group_size=size)
    solver.ensure((group_id[:, :-1] == group_id[:, 1:]) == (is_black[:, :-1] == is_black[:, 1:]))
    solver.ensure((group_id[:-1, :] == group_id[1:, :]) == (is_black[:-1, :] == is_black[1:, :]))

    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:

                right_equals_top = solver.bool_var()
                bottom_equals_top = solver.bool_var()
                bottom_equals_right = solver.bool_var()
                left_equals_top = solver.bool_var()
                left_equals_right = solver.bool_var()
                left_equals_bottom = solver.bool_var()

                if y == 0 or x == width - 1:
                    solver.ensure(~right_equals_top)
                else:
                    solver.ensure(right_equals_top == (group_id[y - 1, x] == group_id[y, x + 1]))

                if y == 0 or y == height - 1:
                    solver.ensure(~bottom_equals_top)
                else:
                    solver.ensure(bottom_equals_top == (group_id[y - 1, x] == group_id[y + 1, x]))

                if y == height - 1 or x == width - 1:
                    solver.ensure(~bottom_equals_right)
                else:
                    solver.ensure(bottom_equals_right == (group_id[y, x + 1] == group_id[y + 1, x]))

                if y == 0 or x == 0:
                    solver.ensure(~left_equals_top)
                else:
                    solver.ensure(left_equals_top == (group_id[y - 1, x] == group_id[y, x - 1]))

                if x == 0 or x == width - 1:
                    solver.ensure(~left_equals_right)
                else:
                    solver.ensure(left_equals_right == (group_id[y, x + 1] == group_id[y, x - 1]))

                if y == height - 1 or x == 0:
                    solver.ensure(~left_equals_bottom)
                else:
                    solver.ensure(left_equals_bottom == (group_id[y + 1, x] == group_id[y, x - 1]))

                top_contribution = solver.int_var(0, height * width)
                right_contribution = solver.int_var(0, height * width)
                bottom_contribution = solver.int_var(0, height * width)
                left_contribution = solver.int_var(0, height * width)

                if y == 0:
                    solver.ensure(top_contribution == 0)
                else:
                    solver.ensure(top_contribution == is_black[y - 1, x].cond(size[y - 1, x], 0))

                if x == width - 1:
                    solver.ensure(right_contribution == 0)
                else:
                    solver.ensure(right_contribution == (is_black[y, x + 1] & ~right_equals_top).cond(size[y, x + 1], 0))

                if y == height - 1:
                    solver.ensure(bottom_contribution == 0)
                else:
                    solver.ensure(bottom_contribution == (is_black[y + 1, x] & ~bottom_equals_top & ~bottom_equals_right).cond(size[y + 1, x], 0))

                if x == 0:
                    solver.ensure(left_contribution == 0)
                else:
                    solver.ensure(left_contribution == (is_black[y, x - 1] & ~left_equals_top & ~left_equals_right & ~left_equals_bottom).cond(size[y, x - 1], 0))

                solver.ensure(top_contribution + right_contribution + bottom_contribution + left_contribution == problem[y][x])

    is_sat = solver.solve()
    return is_sat, is_black


def generate_kurotto(
    height, width, disallow_adjacent=False, symmetry=False, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_kurotto(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(-2, 16),
            default=-2,
            disallow_adjacent=disallow_adjacent,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=-2, weight=4),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 8
        width = 8
        problem = [
            [-1, -2,  0,  1,  2, -2, -2, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2],
            [10, -2, -2, -2, -2, -2, -2,  3],
            [-2, -2, -2, -2, -2, -2, -2,  4],
            [-2, -2, -2, -2, -2, -2, -2, -2],
            [ 9, -2, -2, -2, -2, -2, -2,  5],
            [ 8, -2, -2, -2, -2, -2, -2,  6],
            [-2, -2, -2,  7, -2, -2, -2, -2],
        ]
        is_sat, is_black = solve_kurotto(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        for _ in range(10):
            try:
                problem = generate_kurotto(height, width, disallow_adjacent=False, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, lambda x: "." if x == -2 else 'X' if x == -1 else str(x)), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
