import random
import math
import sys
import numpy as np

from cspuz import Solver
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_battlestar(n, k, clues):
    solver = Solver()
    has_star = solver.bool_array((n, n))
    solver.add_answer_key(has_star)

    for i in range(n):
        solver.ensure(sum(has_star[i, :].cond(1, 0)) == k)
        solver.ensure(sum(has_star[:, i].cond(1, 0)) == k)
    solver.ensure(~(has_star[:-1, :] & has_star[1:, :]))
    solver.ensure(~(has_star[:, :-1] & has_star[:, 1:]))
    solver.ensure(~(has_star[:-1, :-1] & has_star[1:, 1:]))
    solver.ensure(~(has_star[:-1, 1:] & has_star[1:, :-1]))
    
    for y in range(n):
        for x in range(n):
            if clues[y][x] != '..':
                solver.ensure(~has_star[y, x])
            if clues[y][x] in ['00', '01', '02']:
                solver.ensure(count_true(has_star.four_neighbors(y, x)) == int(clues[y][x]))

    is_sat = solver.solve()
    return is_sat, has_star


def _main():
    if len(sys.argv) == 1:
        # generated example: http://pzv.jp/p.html?starbattle/6/6/1/2u9gn9c9jpmk
        is_sat, has_star = solve_battlestar(
            6,
            1,
            [
                ['..', '01', '..', '..', '..', '..'],
                ['..', '..', '..', '..', '..', '..'],
                ['..', '..', '..', '01', '..', '..'],
                ['..', '..', '00', '..', '..', '..'],
                ['..', '..', '..', '..', '..', '..'],
                ['..', '..', '..', '..', '00', '..'],
            ]
        )
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(has_star, {None: "?", True: "*", False: "."}))
    else:
        pass

if __name__ == "__main__":
    _main()
