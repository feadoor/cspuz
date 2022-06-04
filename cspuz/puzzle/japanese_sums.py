import sys

from cspuz import Solver
from cspuz.constraints import fold_and, count_true
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.puzzle import util

def solve_japanese_sums(height, width, n, clue_rows, clue_cols):
    solver = Solver()
    answer = solver.int_array((height, width), 0, n)
    shaded = solver.bool_array((height, width))
    solver.ensure(shaded == (answer == 0))
    solver.add_answer_key(answer, shaded)

    def part_of_group(cells, cell_idx, group_idx):
        return count_true((cells[:cell_idx] != 0) & (cells[1 : cell_idx + 1] == 0)) == group_idx

    def sum_constraint(cells, clue, clue_idx):
        acc = 0
        for cell_idx in range(len(cells)):
            acc += part_of_group(cells, cell_idx, clue_idx).cond(cells[cell_idx], 0)
        return acc == clue

    def japanese_sums(cells, clues):
        return fold_and(sum_constraint(cells, clue, clue_idx) for clue_idx, clue in enumerate(clues) if clue > -1)

    def n_groups(shaded, n):
        sz = len(shaded)
        return count_true((~shaded)[:sz-1] & shaded[1:]) == shaded[sz-1].cond(n, n - 1)

    def no_repeats(cells):
        return fold_and(count_true(cells == v) <= 1 for v in range(1, n + 1))

    for row in range(height):
        solver.ensure(no_repeats(answer[row, :]))
        if clue_rows[row]:
            solver.ensure(n_groups(shaded[row, :], len(clue_rows[row])))
            solver.ensure(japanese_sums(answer[row, :], clue_rows[row]))

    for col in range(width):
        solver.ensure(no_repeats(answer[:, col]))
        if clue_cols[col]:
            solver.ensure(n_groups(shaded[:, col], len(clue_cols[col])))
            solver.ensure(japanese_sums(answer[:, col], clue_cols[col]))

    is_sat = solver.solve()
    return is_sat, answer, shaded


def _main():
    height, width, n = 9, 9, 9
    clue_rows = [[10, 33], [25, 17], [16, 10], [2, 9, 4], [7, 5, 3], [6, 1, 8], [27, 12], [13, 12], [15, 29]]
    clue_cols = [[12, 7, 20], [25, 16], [], [2, 7, 6], [9, 5, 1], [4, 3, 8], [], [20, 17], [14, 13, 9]]
    is_sat, answer, shaded = solve_japanese_sums(height, width, n, clue_rows, clue_cols)
    if is_sat:
        print(util.stringify_array(answer, lambda x: "." if x == 0 else str(x)))
    else:
        print("No solution")


if __name__ == "__main__":
    _main()
