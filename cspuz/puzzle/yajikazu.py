import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, Choice

def solve_yajikazu(height, width, problem):
    solver = Solver()

    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_not_adjacent(solver, is_black)
    graph.active_vertices_connected(solver, ~is_black)

    for y in range(height):
        for x in range(width):
            if problem[y][x] != '..':
                if problem[y][x][0] == '^':
                    solver.ensure((~is_black[y, x]).then(count_true(is_black[:y, x]) == int(problem[y][x][1:])))
                elif problem[y][x][0] == 'v':
                    solver.ensure((~is_black[y, x]).then(count_true(is_black[y:, x]) == int(problem[y][x][1:])))
                elif problem[y][x][0] == '<':
                    solver.ensure((~is_black[y, x]).then(count_true(is_black[y, :x]) == int(problem[y][x][1:])))
                elif problem[y][x][0] == '>':
                    solver.ensure((~is_black[y, x]).then(count_true(is_black[y, x:]) == int(problem[y][x][1:])))

    is_sat = solver.solve()
    return is_sat, is_black


def generate_yajikazu(height, width, verbose=False):
    choices = []
    for y in range(height):
        row = []
        for x in range(width):
            c = [".."]
            for i in range(0, (y + 3) // 2):
                c.append("^{}".format(i))
            for i in range(0, (x + 3) // 2):
                c.append("<{}".format(i))
            for i in range(0, (height - y + 2) // 2):
                c.append("v{}".format(i))
            for i in range(0, (width - x + 2) // 2):
                c.append(">{}".format(i))
            row.append(Choice(c, ".."))
        choices.append(row)
    generated = generate_problem(
        lambda problem: solve_yajikazu(height, width, problem),
        builder_pattern=choices,
        clue_penalty=lambda problem: count_non_default_values(problem, default="..", weight=10),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        height = 6
        width = 6
        problem = [
            ['v1', 'v1', '..', '..', 'v3', '<1'],
            ['..', '..', '..', '..', '..', '..'],
            ['>2', '..', '..', '..', '..', 'v2'],
            ['>2', '..', '..', '..', '..', '<2'],
            ['..', '..', '..', '..', '..', '..'],
            ['^3', '^3', '..', '..', '^3', '^1'],
        ]
        is_sat, is_black = solve_yajikazu(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        for _ in range(10):
            try:
                problem = generate_yajikazu(height, width, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, str), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
