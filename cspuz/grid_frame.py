from cspuz.constraints import BoolVars
from cspuz.grid import BoolGrid


class BoolGridFrame(object):
    """
    Frame of `height` * `width` grid, each of whose edges is associated with a bool variable.
    """
    def __init__(self, solver, height, width):
        self.solver = solver
        self.height = height
        self.width = width
        self.edges = []
        self._all_edges = []
        for y in range(2 * height + 1):
            row = []
            for x in range(2 * width + 1):
                if y % 2 != x % 2:
                    v = solver.bool_var()
                    row.append(v)
                    self._all_edges.append(v)
                else:
                    row.append(None)
            self.edges.append(row)

    def __getitem__(self, item):
        y, x = item
        return self.edges[y][x]

    def all_edges(self):
        return BoolVars(self._all_edges)

    def single_loop(self):
        solver = self.solver
        height = self.height
        width = self.width
        ranks = [[solver.int_var(0, (height + 1) * (width + 1) - 1) for _ in range(width + 1)] for _ in range(height + 1)]
        passed = BoolGrid(solver, height + 1, width + 1)
        is_root = [[solver.bool_var() for _ in range(width + 1)] for _ in range(height + 1)]
        for y in range(height + 1):
            for x in range(width + 1):
                neighbor_edges = []
                if y > 0:
                    neighbor_edges.append((2 * y - 1, 2 * x))
                if y < height:
                    neighbor_edges.append((2 * y + 1, 2 * x))
                if x > 0:
                    neighbor_edges.append((2 * y, 2 * x - 1))
                if x < width:
                    neighbor_edges.append((2 * y, 2 * x + 1))
                degree = sum(map(lambda p: self[p].cond(1, 0), neighbor_edges))
                solver.ensure(degree == passed[y, x].cond(2, 0))
                solver.ensure(passed[y, x].then(sum(map(lambda p: (self[p] & (ranks[p[0] - y][p[1] - x] >= ranks[y][x])).cond(1, 0),
                                                        neighbor_edges)) <= is_root[y][x].cond(2, 1)))
        solver.ensure(sum(map(lambda v: v.cond(1, 0), sum(is_root, []))) == 1)
        return passed