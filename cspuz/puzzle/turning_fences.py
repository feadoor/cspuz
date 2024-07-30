import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.grid_frame import BoolGridFrame
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.problem_serializer import (
    Grid,
    OneOf,
    Spaces,
    IntSpaces,
    serialize_problem_as_url,
    deserialize_problem_as_url,
)

def solve_turning_fences(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height, width)
    solver.add_answer_key(grid_frame)
    graph.active_edges_single_cycle(solver, grid_frame)

    is_turn = solver.bool_array((height + 1, width + 1))
    for y in range(height + 1):
        for x in range(width + 1):
            vertical_edges = [grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < height]
            horizontal_edges = [grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < width]
            solver.ensure(is_turn[y, x] == ((count_true(vertical_edges) == 1) & (count_true(horizontal_edges) == 1)))

    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                vertices = [(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)]
                solver.ensure(count_true(is_turn[b, a] for b, a in vertices) == problem[y][x])

    is_sat = solver.solve()
    return is_sat, grid_frame

def generate_turning_fences(height, width, symmetry=False, verbose=False, disallow_adjacent=False):

    generated = generate_problem(
        lambda problem: solve_turning_fences(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(-1, 5),
            default=-1,
            symmetry=symmetry,
            disallow_adjacent=disallow_adjacent,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=-1, weight=5),
        verbose=verbose,
    )
    return generated

TURNING_FENCES_COMBINATOR = Grid(OneOf(Spaces(-1, "g"), IntSpaces(-1, max_int=4, max_num_spaces=2)))

def serialize_turning_fences(problem):
    height = len(problem)
    width = len(problem[0])
    return serialize_problem_as_url(TURNING_FENCES_COMBINATOR, "vslither", height, width, problem)

def deserialize_turning_fences(url):
    return deserialize_problem_as_url(TURNING_FENCES_COMBINATOR, url, allowed_puzzles="slither")

def _main():
    if len(sys.argv) == 1:
        height = 10
        width = 10
        # fmt: off
        problem = [
            [-1, -1,  1, -1, -1, -1, -1,  2, -1, -1],
            [-1,  3, -1,  3, -1, -1,  1, -1,  1, -1],
            [ 1, -1, -1, -1,  1, -1, -1,  2, -1,  2],
            [-1,  3, -1,  3, -1, -1, -1, -1,  1, -1],
            [-1, -1,  1, -1,  1,  2, -1, -1, -1, -1],
            [-1, -1, -1, -1,  1,  2, -1,  3, -1, -1],
            [-1,  1, -1, -1, -1, -1,  1, -1,  1, -1],
            [ 2, -1,  1, -1, -1,  2, -1, -1, -1,  3],
            [-1,  2, -1,  1, -1, -1,  1, -1,  1, -1],
            [-1, -1,  2, -1, -1, -1, -1,  3, -1, -1],
        ]
        # fmt: on
        is_sat, is_line = solve_turning_fences(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        cspuz.config.solver_timeout = 1800.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_turning_fences(height, width, symmetry=True, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, {-1: ".", 0: "0", 1: "1", 2: "2", 3: "3", 4: "4"}))
                    print(serialize_turning_fences(problem))
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
