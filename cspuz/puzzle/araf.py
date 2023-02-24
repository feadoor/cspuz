import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D

def solve_araf(height, width, problem):

    solver = Solver()

    max_clue, clues = 0, []
    for y in range(height):
        for x in range(width):
            if problem[y][x] > 0:
                clues.append((y, x, problem[y][x]))
                max_clue = max(max_clue, problem[y][x])

    blocks = []
    for (y, x, _) in clues:
        block = solver.bool_array((height, width));
        graph.active_vertices_connected(solver, block)
        solver.ensure(block[y, x])
        blocks.append(block)

    for i in range(len(blocks)):
        size = solver.int_var(1, max_clue - 1)
        solver.ensure(count_true(blocks[i][:, :]) == size)

        for j in range(i + 1, len(blocks)):
            (yi, xi, ni), (yj, xj, nj) = clues[i], clues[j]
            if abs(ni - nj) <= 1:
                solver.ensure(~blocks[i][yj, xj])
                solver.ensure(~blocks[j][yi, xi])
            else:
                lo, hi = min(ni, nj), max(ni, nj)
                solver.ensure(
                    ((blocks[i][yj, xj]) | (blocks[j][yi, xi])).then(
                        (blocks[i][:, :] == blocks[j][:, :]) & (size > lo) & (size < hi)
                    )
                )

    for y in range(height):
        for x in range(width):
            indicators = [block[y, x] for block in blocks]
            solver.ensure(count_true(indicators) == 2)

    for block in blocks:
        solver.add_answer_key(block)

    is_sat = solver.solve()
    return is_sat, blocks

def main():
    if len(sys.argv) == 1:
        height, width = 6, 6
        problem = [
            [0, 0, 3, 0, 0, 0],
            [0, 3, 0, 0, 0, 0],
            [3, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 28],
            [0, 0, 0, 0, 8, 0],
            [0, 0, 0, 8, 0, 0],
        ]
        is_sat, blocks = solve_araf(height, width, problem)
        if is_sat:
            print('Has solution')
            for y in range(len(problem)):
                for x in range(len(problem[y])):
                    block_index = min((i for i in range(len(blocks)) if blocks[i][y, x].sol), default=-1)
                    if block_index == -1:
                        print("_", end="")
                    else:
                        print("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[block_index], end="")
                print()
            print()

if __name__ == "__main__":
    main()
