import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.grid_frame import BoolGridFrame
from cspuz.constraints import fold_or
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_balance(height, width, problem):

    def line_length(edges):
        edges = list(edges)
        if len(edges) == 0:
            return solver.int_var(0, 0)
        ret = edges[-1].cond(1, 0)
        for i in range(len(edges) - 2, -1, -1):
            ret = edges[i].cond(1 + ret, 0)
        return ret

    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)
    is_passed = graph.active_edges_single_cycle(solver, grid_frame)

    for y in range(height):
        for x in range(width):
            if problem[y][x] != 0:
                
                solver.ensure(is_passed[y, x])

                left_line = line_length(reversed(list(grid_frame.horizontal[y, :x])))
                right_line = line_length(grid_frame.horizontal[y, x:])
                up_line = line_length(reversed(list(grid_frame.vertical[:y, x])))
                down_line = line_length(grid_frame.vertical[y:, x])

                if problem[y][x] > 0:
                    solver.ensure(((left_line > 0) & (right_line > 0)).then(left_line == right_line))
                    solver.ensure(((left_line > 0) & (up_line > 0)).then(left_line == up_line))
                    solver.ensure(((left_line > 0) & (down_line > 0)).then(left_line == down_line))
                    solver.ensure(((right_line > 0) & (up_line > 0)).then(right_line == up_line))
                    solver.ensure(((right_line > 0) & (down_line > 0)).then(right_line == down_line))
                    solver.ensure(((up_line > 0) & (down_line > 0)).then(up_line == down_line))

                    if problem[y][x] > 1:
                        solver.ensure(left_line + right_line + up_line + down_line == problem[y][x])

                elif problem[y][x] < 0:
                    solver.ensure(((left_line > 0) & (right_line > 0)).then(left_line != right_line))
                    solver.ensure(((left_line > 0) & (up_line > 0)).then(left_line != up_line))
                    solver.ensure(((left_line > 0) & (down_line > 0)).then(left_line != down_line))
                    solver.ensure(((right_line > 0) & (up_line > 0)).then(right_line != up_line))
                    solver.ensure(((right_line > 0) & (down_line > 0)).then(right_line != down_line))
                    solver.ensure(((up_line > 0) & (down_line > 0)).then(up_line != down_line))

                    if problem[y][x] < -1:
                        solver.ensure(left_line + right_line + up_line + down_line == -problem[y][x])

    is_sat = solver.solve()
    return is_sat, grid_frame


def generate_balance(height, width, symmetry=True, verbose=False):
    generated = generate_problem(
        lambda problem: solve_balance(height, width, problem),
        builder_pattern=ArrayBuilder2D(height, width, range(-9, 10), default=0, symmetry=symmetry),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=8),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 10
        width = 10
        problem = [
            [ 0,  0,  0,  0,  0,  1,  0, -1,  0,  0],
            [ 1,  1,  0,  0,  1,  0, -1,  0,  1,  0],
            [-1,  0,  0,  1,  0, -1,  0,  0, -1,  1],
            [ 0,  1,  1,  0, -1,  0,  0,  0,  1,  0],
            [ 0,  1,  0, -1,  0,  0,  0,  1,  0, -1],
            [ 1,  0, -1,  0,  0,  0,  1,  0, -1,  0],
            [ 0, -1,  0,  0,  0,  1,  0, -1, -1,  0],
            [-1,  1,  0,  0,  1,  0, -1,  0,  0,  1],
            [ 0, -1,  0,  1,  0, -1,  0,  0, -1, -1],
            [ 0,  0,  1,  0, -1,  0,  0,  0,  0,  0],
        ]
        is_sat, is_line = solve_balance(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        cspuz.config.solver_timeout = 600.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_balance(height, width, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, lambda x: "." if x == 0 else str(x)))
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
