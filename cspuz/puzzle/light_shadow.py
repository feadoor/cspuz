from cspuz import Solver, graph, count_true
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.puzzle import util
import sys

def solve_light_shadow(height, width, problem):
    solver = Solver()
    clues = []
    for y in range(height):
        for x in range(width):
            if problem[y][x] != 0:
                clues.append((y, x, 0.5 if problem[y][x] == '@' else -0.5 if problem[y][x] == '#' else problem[y][x]))
    
    shaded = solver.bool_array((height, width))
    solver.add_answer_key(shaded)
    if len(clues) == 0: return False, shaded

    division = solver.int_array((height, width), 0, len(clues) - 1)
    roots = list(map(lambda x: (x[0], x[1]), clues))
    graph.division_connected(solver, division, len(clues), roots=roots)


    for y in range(height):
        for x in range(width):
            for b, a in [(b, a) for (b, a) in [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)] if 0 <= b < height and 0 <= a < width]:
                solver.ensure((shaded[y, x] == shaded[b, a]) == (division[y, x] == division[b, a]))

    for i, (y, x, n) in enumerate(clues):
        if n >= 1 or n <= -1: solver.ensure(count_true(division == i) == abs(n))
        if n > 0: solver.ensure(~shaded[y, x])
        if n < 0: solver.ensure(shaded[y, x])

    is_sat = solver.solve()
    return is_sat, shaded

def generate_light_shadow(height, width, min_clue=1, max_clue=15, symmetry=True, verbose=False):
    return generate_problem(
        lambda problem: solve_light_shadow(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            list(range(-max_clue, -min_clue + 1)) + [-0.5, 0, 0.5] + list(range(min_clue, max_clue + 1)),
            default=0,
            disallow_adjacent=True,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=3),
        verbose=verbose,
    )

def main():
    if len(sys.argv) == 1:
        height, width = 12, 12
        problem = [
            [  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
            [  7, -4,  7,  0,  0,  0,  0,  0,  0,  0,  0,  0],
            [  0,  0,  0,  0,  0,  0,  0,  0, -7,  4, -6,  0],
            [  0,  0, -9,  5, -9,  0,  0,  0,  0,  0,  0,  0],
            [  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
            [  0,  0,  0,  0,'@',  0,  0,'#',  0,  0,  0,  0],
            [  0,  0,  0,  0,'#',  0,  0,'@',  0,  0,  0,  0],
            [  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
            [  0,  0,  0,  0,  0,  0,  0, -6,  5, -6,  0,  0],
            [  0, -9,  7, -8,  0,  0,  0,  0,  0,  0,  0,  0],
            [  0,  0,  0,  0,  0,  0,  0,  0,  0,  9, -3,  9],
            [  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        ]

        is_sat, shaded = solve_light_shadow(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(shaded, {None: "?", True: "#", False: "."}))

    else:
        height, width = int(sys.argv[1]), int(sys.argv[2])
        while True:
            problem = generate_light_shadow(height, width, min_clue=2, max_clue=16, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, lambda x: "." if x == 0 else "#" if x == -0.5 else "@" if x == 0.5 else str(x)), flush=True)
                _, shaded = solve_light_shadow(height, width, problem)
                print()
                print(util.stringify_array(shaded, {None: "?", True: "#", False: "."}), flush=True)
            print(flush=True)

if __name__ == '__main__':
    main()
