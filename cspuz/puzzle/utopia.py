import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D

def solve_utopia(height, width, problem):
    solver = Solver()

    clues = []
    for y in range(height):
        for x in range(width):
            if problem[y][x] > 0:
                clues.append((y, x, problem[y][x]))

    division = solver.int_array((height, width), 0, len(clues) - 1)
    roots = list(map(lambda x: (x[0], x[1]), clues))
    graph.division_connected(solver, division, len(clues), roots=roots)

    tl_square = solver.bool_array((height, width))

    for y in range(height):
        for x in range(width):
            if y == height - 1 or x == width - 1:
                solver.ensure(~tl_square[y, x])
            else:
                solver.ensure(tl_square[y, x] == ((division[y, x] == division[y, x + 1]) & (division[y, x] == division[y + 1, x]) & (division[y, x] == division[y + 1, x + 1])))


    for i, (y, x, v) in enumerate(clues):
        solver.ensure(count_true(tl_square[:, :] & (division[:, :] == i)) == 1)
        if v > 1:
            solver.ensure(count_true(division[:, :] == i) == v)

    for y in range(height):
        for x in range(width):
            for (b, a) in [(y - 2, x - 1), (y - 2, x), (y - 2, x + 1), (y - 1, x - 2), (y - 1, x - 1), (y - 1, x), (y - 1, x + 1), (y - 1, x + 2), (y, x - 2), (y, x - 1), (y, x + 1), (y, x + 2), (y + 1, x - 2), (y + 1, x - 1), (y + 1, x), (y + 1, x + 1), (y + 1, x + 2), (y + 2, x - 1), (y + 2, x), (y + 2, x + 1)]:
                if 0 <= b < height and 0 <= a < width:
                    solver.ensure((~tl_square[y, x]) | (~tl_square[b, a]))

    solver.add_answer_key(division)
    is_sat = solver.solve()
    return is_sat, division

def generate_utopia(height, width, max_clue=15, verbose=True):
    generated = generate_problem(
        lambda problem: solve_utopia(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            [0, 1] + list(range(4, max_clue + 1)),
            default=0,
            disallow_adjacent=False,
            symmetry=False,
            initial=[
                [10, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 10],
            ]
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=10),
        verbose=verbose,
    )
    return generated

def main():
    if len(sys.argv) == 1:
        height, width = 9, 9
        problem = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 8, 0, 0, 0, 0, 0, 4, 0],
            [0, 8, 0, 0, 0, 0, 0, 5, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 8, 0, 0, 0, 0, 0, 7, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 28, 0, 0, 0, 7, 0, 0],
            [0, 0, 0, 0, 6, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        is_sat, division = solve_utopia(height, width, problem)
        if is_sat:
            print('Has solution')
            for y in range(len(problem)):
                for x in range(len(problem[y])):
                    if division[y, x].sol == None:
                        print("_", end="")
                    else:
                        print("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[division[y, x].sol], end="")
                print()
            print()
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_utopia(height, width)
            if problem is not None:
                print(
                    util.stringify_array(
                        problem, lambda x: "." if x == 0 else ("?" if x == 1 else str(x))
                    ),
                    flush=True,
                )
                print(flush=True)

if __name__ == "__main__":
    main()
