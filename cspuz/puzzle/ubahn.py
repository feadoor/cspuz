from cspuz import Solver, graph
from cspuz.array import IntArray2D
from cspuz.constraints import count_true
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util

EMPTY = 0
TURN = 1
LINE = 2
T_JUNCTION = 3
CROSS = 4

def solve_ubahn(height, width, row_clues, col_clues):
    
    solver = Solver()
    type = solver.int_array((height, width), 0, 4)
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)

    def is_empty(cell):
        (y, x) = cell
        return count_true(grid_frame.vertex_neighbors(y, x)) == 0
    
    def is_turn(cell):
        (y, x) = cell
        vertical_edges = [grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < height - 1]
        horizontal_edges = [grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < width - 1]
        return (count_true(vertical_edges) == 1) & (count_true(horizontal_edges) == 1)
    
    def is_line(cell):
        (y, x) = cell
        vertical_edges = [grid_frame.vertical[b, x] for b in [y, y - 1] if 0 <= b < height - 1]
        horizontal_edges = [grid_frame.horizontal[y, a] for a in [x, x - 1] if 0 <= a < width - 1]
        return (
            (count_true(vertical_edges) == 2) & (count_true(horizontal_edges) == 0) |
            (count_true(vertical_edges) == 0) & (count_true(horizontal_edges) == 2)
        )
    
    def is_t_junction(cell):
        (y, x) = cell
        return count_true(grid_frame.vertex_neighbors(y, x)) == 3

    def is_cross(cell):
        (y, x) = cell
        return count_true(grid_frame.vertex_neighbors(y, x)) == 4

    for y in range(height):
        for x in range(width):
            solver.ensure(count_true(grid_frame.vertex_neighbors(y, x)) != 1)
            solver.ensure(is_empty((y, x)).then(type[y, x] == EMPTY))
            solver.ensure(is_turn((y, x)).then(type[y, x] == TURN))
            solver.ensure(is_line((y, x)).then(type[y, x] == LINE))
            solver.ensure(is_t_junction((y, x)).then(type[y, x] == T_JUNCTION))
            solver.ensure(is_cross((y, x)).then(type[y, x] == CROSS))

    graph.active_edges_connected(solver, grid_frame)
    for (idx, ty, val) in row_clues:
        solver.ensure(count_true(type[idx, :] == ty) == val)
    for (idx, ty, val) in col_clues:
        solver.ensure(count_true(type[:, idx] == ty) == val)


    is_sat = solver.solve()
    return is_sat, grid_frame
    
def main():
    height = 6
    width = 6

    row_clues = [(0, T_JUNCTION, 1), (1, CROSS, 1), (1, T_JUNCTION, 0), (2, LINE, 0), (3, T_JUNCTION, 0), (3, TURN, 0), (4, CROSS, 0), (4, LINE, 1), (4, TURN, 1), (5, T_JUNCTION, 1)]
    col_clues = [(0, LINE, 1), (1, CROSS, 1), (1, TURN, 0), (2, LINE, 0), (4, TURN, 0), (5, LINE, 1)]

    is_sat, grid_frame = solve_ubahn(height, width, row_clues, col_clues)
    print("has answer:", is_sat)
    if is_sat:
        print(util.stringify_grid_frame(grid_frame))

if __name__ == '__main__':
    main()
