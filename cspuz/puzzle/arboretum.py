from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util

def solve_arboretum(height, width, clues, edges):

    solver = Solver()

    # Create a graph representing the grid, respecting given edges
    g = graph.Graph(height * width)
    for y in range(height):
        for x in range(width):
            if x < width - 1 and ((y, x), (y, x + 1)) not in edges and ((y, x + 1), (y, x)) not in edges:
                g.add_edge(y * width + x, y * width + (x + 1))
            if y < height - 1 and ((y, x), (y + 1, x)) not in edges and ((y + 1, x), (y, x)) not in edges:
                g.add_edge(y * width + x, (y + 1) * width + x)

    # The solution is a spanning forest with each tree containing one of the given clues
    roots = [c[0][0] * width + c[0][1] for c in clues]
    _is_root = solver.bool_array(height * width)
    for n in range(height * width): solver.ensure(_is_root[n] == (n in roots))

    _division = solver.int_array(height * width, 0, len(clues) - 1)
    spanning_forest, _is_leaf = graph.division_connected(solver, _division, len(clues), roots=roots, graph=g)
    division, is_leaf, is_root = _division.reshape((height, width)), _is_leaf.reshape((height, width)), _is_root.reshape((height, width))
    solver.add_answer_key(spanning_forest)

    # Leaves belonging to the same tree must not share a row or column, and there must be the right number of leaves
    for i, ((y, x), v) in enumerate(clues):
        solver.ensure(division[y, x] == i)
        for c in range(width):
            solver.ensure(count_true((division[:, c] == i) & is_leaf[:, c] & ~is_root[:, c]) <= 1)
        for r in range(height):
            solver.ensure(count_true((division[r, :] == i) & is_leaf[r, :] & ~is_root[r, :]) <= 1)
        if v > 0:
            solver.ensure(count_true((division[:, :] == i) & is_leaf[:, :] & ~is_root[:, :]) == v)
        else:
            solver.ensure(count_true((division[:, :] == i) & is_leaf[:, :] & ~is_root[:, :]) > 0)

    is_sat = solver.solve()
    return is_sat, g, spanning_forest

def run(height, width, clues, edges):
    is_sat, g, forest = solve_arboretum(height, width, clues, edges)

    if any(e.sol == None for e in forest):
        print("Non-unique!")
    else:
        print("Unique!")

    edge_map = {}
    for e in range(len(forest)):
        v1, v2 = g[e]
        edge_map[((v1 // width, v1 % width), (v2 // width, v2 % width))] = e

    solution_str = []

    for x in range(width):
        solution_str.append('.   ')
    solution_str.append('.\n')

    for y in range(height):
        solution_str.append('  ')
        for x in range(width):
            if x < width - 1 and ((y, x), (y, x + 1)) in edge_map and forest[edge_map[((y, x), (y, x + 1))]].sol:
                solution_str.append('----')
            else:
                solution_str.append('    ')
        solution_str.append('\n')
        for x in range(width):
            if y < height - 1 and ((y, x), (y + 1, x)) in edge_map and forest[edge_map[((y, x), (y + 1, x))]].sol:
                solution_str.append('. | ')
            else:
                solution_str.append('.   ')
        solution_str.append('.\n')

    print(''.join(solution_str))

height, width = (10, 10)
clues = [((0, 0), 3), ((1, 2), 6), ((2, 4), 9), ((7, 3), 10), ((8, 6), 7), ((9, 9), 4)]
edges = [((1, 0), (1, 1)), ((1, 3), (1, 4)), ((1, 6), (1, 7)), ((2, 5), (2, 6)), ((2, 7), (2, 8)), ((3, 1), (3, 2)), ((4, 3), (4, 4)), ((4, 5), (4, 6)), ((4, 8), (4, 9)), ((6, 1), (6, 2)), ((6, 3), (6, 4)), ((6, 6), (6, 7)), ((8, 1), (8, 2)), ((8, 4), (8, 5)), ((8, 7), (8, 8)), ((9, 8), (9, 9)), ((3, 1), (4, 1)), ((6, 1), (7, 1)), ((7, 2), (8, 2)), ((1, 3), (2, 3)), ((4, 3), (5, 3)), ((5, 4), (6, 4)), ((2, 5), (3, 5)), ((7, 5), (8, 5)), ((3, 6), (4, 6)), ((5, 7), (6, 7)), ((1, 8), (2, 8)), ((7, 8), (8, 8))]

run(height, width, clues, edges)
