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

def solve_kurotto(height, width, problem):
    solver = Solver()

    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)

    for y in range(height):
        for x in range(width):
            if problem[y][x] > -2:
                solver.ensure(~is_black[y, x])

    group_id, size = graph.connected_groups(solver, is_black)

    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                nbrs = [(a, b) for (a, b) in [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)] if 0 <= a < height and 0 <= b < width]
                for a, b in nbrs:
                    solver.ensure(size[a, b] <= problem[y][x])
                solver.ensure(sum(size[a, b] for (a, b) in nbrs) >= problem[y][x])

                has_top_nbr, has_right_nbr, has_bottom_nbr, has_left_nbr = (y > 0, x < width - 1, y < height - 1, x > 0)
                right_eq_top = (group_id[y, x + 1] == group_id[y - 1, x]) if (has_right_nbr and has_top_nbr) else false_variable(solver)
                bottom_eq_top = (group_id[y + 1, x] == group_id[y - 1, x]) if (has_bottom_nbr and has_top_nbr) else false_variable(solver)
                bottom_eq_right = (group_id[y + 1, x] == group_id[y, x + 1]) if (has_bottom_nbr and has_right_nbr) else false_variable(solver)
                left_eq_top = (group_id[y, x - 1] == group_id[y - 1, x]) if (has_left_nbr and has_top_nbr) else false_variable(solver)
                left_eq_right = (group_id[y, x - 1] == group_id[y, x + 1]) if (has_left_nbr and has_right_nbr) else false_variable(solver)
                left_eq_bottom = (group_id[y, x - 1] == group_id[y + 1, x]) if (has_left_nbr and has_bottom_nbr) else false_variable(solver)

                total_size = 0
                if has_top_nbr:
                    total_size += size[y - 1, x]
                if has_right_nbr:
                    total_size += (~right_eq_top).cond(size[y, x + 1], 0)
                if has_bottom_nbr:
                    total_size += (~bottom_eq_top & ~bottom_eq_right).cond(size[y + 1, x], 0)
                if has_left_nbr:
                    total_size += (~left_eq_top & ~left_eq_right & ~left_eq_bottom).cond(size[y, x - 1], 0)
                solver.ensure(total_size == problem[y][x])

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
