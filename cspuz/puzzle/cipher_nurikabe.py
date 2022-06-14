import argparse
import sys
import subprocess

import cspuz
from cspuz import Solver, graph, count_true, alldifferent
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.problem_serializer import (
    Grid,
    OneOf,
    Spaces,
    HexInt,
    Dict,
    serialize_problem_as_url,
    deserialize_problem_as_url,
)


def solve_cipher_nurikabe(height, width, problem):
    solver = Solver()
    ciphers = {}
    clues = []

    for y in range(height):
        for x in range(width):
            if problem[y][x] != 0:
                clues.append((y, x, problem[y][x]))
    division = solver.int_array((height, width), 0, len(clues))

    roots = [None] + list(map(lambda x: (x[0], x[1]), clues))
    graph.division_connected(solver, division, len(clues) + 1, roots=roots)
    is_black = solver.bool_array((height, width))
    solver.ensure(is_black == (division == 0))
    solver.add_answer_key(is_black)

    for (y, x, c) in clues:
        if c != '?':
            ciphers[c] = solver.int_var(1, height * width)
    solver.ensure(alldifferent(ciphers.values()))

    solver.ensure((~is_black).conv2d(2, 1, "and").then(division[:-1, :] == division[1:, :]))
    solver.ensure((~is_black).conv2d(1, 2, "and").then(division[:, :-1] == division[:, 1:]))
    solver.ensure((~is_black).conv2d(2, 2, "or"))
    for i, (y, x, c) in enumerate(clues):
        if c != '?':
            solver.ensure(count_true(division == (i + 1)) == ciphers[c])

    is_sat = solver.solve()

    return is_sat, is_black


def generate_nurikabe(height, width, max_ciphers=10, verbose=False):
    generated = generate_problem(
        lambda problem: solve_cipher_nurikabe(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            [0] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')[:max_ciphers],
            default=0,
            disallow_adjacent=True,
            symmetry=False,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=5),
        verbose=verbose,
    )
    return generated


NURIKABE_COMBINATOR = Grid(OneOf(Dict([-1], ["."]), Spaces(0, "g"), HexInt()))


def serialize_nurikabe(problem):
    height = len(problem)
    width = len(problem[0])
    return serialize_problem_as_url(NURIKABE_COMBINATOR, "nurikabe", height, width, problem)


def deserialize_nurikabe(url):
    return deserialize_problem_as_url(NURIKABE_COMBINATOR, url, allowed_puzzles="nurikabe")


def main():
    if len(sys.argv) == 1:
        height = 7
        width = 7
        problem = [
            ['E', 0 , 0 , 0 , 0 , 0 , 0 ],
            [ 0 ,'X', 0 , 0 ,'M', 0 , 0 ],
            [ 0 , 0 , 0 ,'A', 0 ,'P', 0 ],
            [ 0 , 0 , 0 , 0,  0 , 0 , 0 ],
            [ 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
            [ 0 , 0 , 0 ,'L', 0 , 0 , 0 ],
            [ 0 , 0 , 0 , 0 , 0 , 0 ,'E'],
        ]
        is_sat, is_black = solve_cipher_nurikabe(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", True: "#", False: "."}))
    else:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--height", type=int)
        parser.add_argument("-w", "--width", type=int)
        parser.add_argument("--max-ciphers", type=int, default=10)
        parser.add_argument("-v", "--verbose", action="store_true")
        args = parser.parse_args()

        height = args.height
        width = args.width
        max_ciphers = args.max_ciphers
        verbose = args.verbose
        cspuz.config.solver_timeout = 1800.0
        while True:
            try:
                problem = generate_nurikabe(
                    height, width, max_ciphers=max_ciphers, verbose=verbose
                )
                if problem is not None:
                    print(
                        util.stringify_array(
                            problem, lambda x: "." if x == 0 else str(x)
                        ),
                        flush=True,
                    )
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    main()
