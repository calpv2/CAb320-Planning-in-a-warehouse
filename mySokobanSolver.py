
'''

    Sokoban assignment


The functions and classes defined in this module will be called by a marker script. 
You should complete the functions and classes according to their specified interfaces.

No partial marks will be awarded for functions that do not meet the specifications
of the interfaces.

You are NOT allowed to change the defined interfaces.
In other words, you must fully adhere to the specifications of the 
functions, their arguments and returned values.
Changing the interfacce of a function will likely result in a fail 
for the test of your code. This is not negotiable! 

You have to make sure that your code works with the files provided 
(search.py and sokoban.py) as your code will be tested 
with the original copies of these files. 

Last modified by 2021-08-17  by f.maire@qut.edu.au
- clarifiy some comments, rename some functions
  (and hopefully didn't introduce any bug!)

'''

# You have to make sure that your code works with 
# the files provided (search.py and sokoban.py) as your code will be tested 
# with these files
import search 
import sokoban


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def my_team():
    '''
    Return the list of the team members of this assignment submission as a list
    of triplet of the form (student_number, first_name, last_name)
    
    '''

    return [(11961511, 'James', 'Galea'), (1234568, 'Pavel', 'Glivinskiy'), (12062863, 'Zachary', 'Allouet') ]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CONSTANTS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
MOVES = {
    'Up': (0, -1),
    'Down': (0, 1),
    'Left': (-1, 0),
    'Right': (1, 0)
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# UTILITY FUNCTIONS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def read_warehouse(warehouse):
    """
    Read Sokoban Warehouse file.
    @param warehouse : str
        path to warehouse file 
    @return: tuple[list[int], list[str]]
                weight list of box weights (length = number of boxes)
                grid_lines: list of strings that represent the warehouse layout
                (each string is a row of the grid).
    """
    with open(warehouse, 'r') as f:
        lines = [line.rstrip('\n') for line in f]

    first_line = lines[0].strip() 
    
    weights = list(map(int, first_line.split()))
    grid_lines = [line[1:] for line in lines[1:]]
    return weights, grid_lines

def get_cell(grid, r, c):
    """
    retrieve a cell from a 2D grid.
    
    If the requested position is out of bounds, a blank space (' ') is returned.
    
    @param grid: list[str]
    
    @param r: int
        row index
    @param c: int
        column index
    
        @return:    str
            characters at position (r, c), or ' ' if out of bounds
    """
    if r < 0 or r >= len(grid):
        return ' '
    if c < 0 or c >= len(grid[r]):
        return ' '
    return grid[r][c]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# REACHABILITY
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def reachable(worker, boxes, walls):  # determining if the box can be reached to push in the desired direction
    """
    compute all reachable positions by the worker whithin the warehouse. 
    
    A graph search is performed (DFS using stack) to determine 
    all positions that the worker can reach.
    
    @param worker: Tuple[int,int]
        initial position of the worker in x,y coordinates 
        
    @param boxes: iterable[tuple[int,int]]
        Positions of boxes 
    
    @param walls: set[tuple[int,int]]
        position of walls
        
    @return:
        set[tuple[int,int]]
            All reachable positions from the workers starting position.
    """
    frontier = [worker]
    visited = set([worker])
    boxes = set(boxes)

    while frontier:
        x, y = frontier.pop()   #take location of worker

        for dx, dy in MOVES.values():  #checks the moves for the worker in all directions
            nx, ny = x + dx, y + dy      
            new_worker = (nx, ny)

            if (new_worker not in visited and    #determines if move is possible and has not already been visited
                new_worker not in walls and
                new_worker not in boxes):
                
                visited.add(new_worker)
                frontier.append(new_worker)

    return visited

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TABOO CELLS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def taboo_cells(wh):
    """
    Identify the taboo cells whithin the warehosue environment.
    
    A taboo cell is a position where placing a box makes the puzzle impossible.
    Two rules follow this implementation:
    
    Rule 1(corners):
        any cell that isnt a target, that is a corner is taboo.

    Rule 2 (wall-aligned segments):
        cells that are in-between 2 corner taboo cells along a row or column are also taboo cells 
        if:
            -none of the cells are target cells.
            -all cells are adjacent to a wall along that direction. 
    @param wh: Warehouse
        Warehouse object with attributes:
        - walls: list[(int, int)]
        - targets: list[(int,int)]
        - worker: (int,int)
        - ncols: int
        - nrows: int
    
    return:
        str
            A string representation of the warehosue environment, where:
            '#' = wall
            'X' = taboo cell
            ' ' = empty space
        """
    walls = set(wh.walls)
    targets = set(wh.targets)

    interior = reachable(wh.worker, [], walls)

    taboo = set()

    for x in range(wh.ncols):
        for y in range(wh.nrows):
            pos = (x, y)

            if pos not in interior or pos in targets:
                continue
              #checks for perpendicular walls to determine corner
            if ((x+1, y) in walls or (x-1, y) in walls) and ((x, y+1) in walls or (x, y-1) in walls):
                taboo.add(pos)

    corners = list(taboo)

    for y in range(wh.nrows):
        row_corners = sorted([x for (x, yy) in corners if yy == y])   #isolate the corners along a row

        for i in range(len(row_corners) - 1):
            x1, x2 = row_corners[i], row_corners[i+1]

            possible = True

            for x in range(x1+1, x2):
                if (x, y) in targets:
                    possible = False
                    break

                if not ((x, y-1) in walls or (x, y+1) in walls):
                    possible = False
                    break

            if possible:
                for x in range(x1+1, x2):
                    taboo.add((x, y))

    for x in range(wh.ncols):
        col_corners = sorted([y for (xx, y) in corners if xx == x])      #isolate the down along a column

        for i in range(len(col_corners) - 1):
            y1, y2 = col_corners[i], col_corners[i+1]

            possible = True

            for y in range(y1+1, y2):
                if (x, y) in targets:
                    possible = False
                    break

                if not ((x-1, y) in walls or (x+1, y) in walls):
                    possible = False
                    break

            if possible:
                for y in range(y1+1, y2):
                    taboo.add((x, y))

    # Build the output string
    X, Y = zip(*wh.walls)
    x_size, y_size = 1 + max(X), 1 + max(Y)
    vis = [[' '] * x_size for _ in range(y_size)]
    for (x, y) in wh.walls:
        vis[y][x] = '#'
    for (x, y) in taboo:
        vis[y][x] = 'X'

    return '\n'.join([''.join(row) for row in vis])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# SOKOBAN PROBLEM
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SokobanPuzzle(search.Problem):
    
    def __init__(self, warehouse, taboo_set):
        """
        @param warehouse: Warehouse
        
        @param taboo_set: set[(int,int)]
        """
        self.warehouse = warehouse
        
        initial = (warehouse.worker, tuple(warehouse.boxes))
        super().__init__(initial)
    
        self.goals = set(warehouse.targets)
        self.walls = set(warehouse.walls)
        self.taboo_set = set(taboo_set)
        self.weights = warehouse.weights
        self.initial_boxes = list(warehouse.boxes)

        self.box_weight = {pos: w for pos, w in zip(warehouse.boxes, warehouse.weights)}


    def actions(self, state):
        """
        Return legal actions from a state.
        
        @param state: Tuple[(int, int), tuple[(int,int)]]
        
        @return:      list[str]
        """
        worker, boxes = state
        boxes = set(boxes)

        #if any box is on a taboo cell and not on a goal, discontinue 
        for box in boxes:
            if box in self.taboo_set and box not in self.goals:
                return []
        acts = []
    
        for move, (dx, dy) in MOVES.items():
            new_worker = (worker[0] + dx, worker[1] + dy)
    
            if new_worker in self.walls:
                continue
    
            if new_worker in boxes:               #verifies the new worker position is where the box was, then the change in worker position is added the box position
                new_box = (new_worker[0] + dx, new_worker[1] + dy)
    
                if (new_box not in self.taboo_set and            #verifies the new box locations is in a valid position
                    new_box not in self.walls and
                    new_box not in boxes):
                    acts.append(move)
            else:
                acts.append(move)
        return acts

    def result(self, state, action):
        """
        Apply legal set of moves.
        
        @param state
        
        @param action: str
        
        @return: new state
        """
        worker, boxes = state
        boxes_list = list(boxes)

        dx, dy = MOVES[action]
        new_worker = (worker[0] + dx, worker[1] + dy)

        if new_worker in set(boxes_list):
            new_box = (new_worker[0] + dx, new_worker[1] + dy)
            idx = boxes_list.index(new_worker)
            boxes_list[idx] = new_box

        return (new_worker, tuple(boxes_list))

    def goal_test(self, state):
        """
        Check if all boxes are on goals.
        """
        _, boxes = state
        return set(boxes) == self.goals

    def h(self, node):
        """
        Heuiristics: weighted Manhattan distance.
        
        @param node
        
        @return: float
        """
        _, boxes = node.state
        boxes = list(boxes)
        goals = list(self.goals)
        weights = self.warehouse.weights

        total = 0

        for (b, w) in zip(boxes, weights):
            dist = min(abs(b[0] - gx) + abs(b[1] - gy)
                    for (gx, gy) in goals)
            total += dist * w

        return total
    
    def path_cost(self, c, state1, action, state2):
        """
        Cost function.
        
        @return: float
        """
        _, boxes1 = state1
        _, boxes2 = state2

        for i, (b1, b2) in enumerate(zip(boxes1, boxes2)):
            if b1 != b2:
                return c + 1 + self.weights[i]

        return c + 1


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# ACTION SEQUENCE CHECKER
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def check_elem_action_seq(warehouse, action_seq):
    '''
    
    Determine if the sequence of actions listed in 'action_seq' is legal or not.
    
    Important notes:
      - a legal sequence of actions does not necessarily solve the puzzle.
      - an action is legal even if it pushes a box onto a taboo cell.
        
    @param warehouse: a valid Warehouse object

    @param action_seq: a sequence of legal actions.
           For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
           
    @return
        The string 'Impossible', if one of the action was not valid.
           For example, if the agent tries to push two boxes at the same time,
                        or push a box into a wall.
        Otherwise, if all actions were successful, return                 
               A string representing the state of the puzzle after applying
               the sequence of actions.  This must be the same string as the
               string returned by the method  Warehouse.__str__()
    '''
    
    ##         "INSERT YOUR CODE HERE"
    moves = {
        'Left':  (-1, 0),
        'Right': (1, 0),
        'Up':    (0, -1),
        'Down':  (0, 1)
    }
    # work on a copy so the original warehouse is not modified
    worker = warehouse.worker
    boxes = list(warehouse.boxes)
    walls = set(warehouse.walls)
    
    for action in action_seq:
        if action not in moves:
            return 'Impossible'
        
        dx, dy = moves[action]
        next_worker = (worker[0] + dx, worker[1] + dy)
        
        #cant move into a wall
        if next_worker in walls:
            return 'Impossible'
        
        #try to push box if there is one
        if next_worker in boxes:
            next_box = (next_worker[0] + dx, next_worker[1] + dy)
            
            # cannot push box into a wall or another box
            if next_box in walls or next_box in boxes:
                return 'Impossible'
            
            #move the box
            box_index = boxes.index(next_worker)
            boxes[box_index] = next_box
        # move the worker
        worker = next_worker
    
    return warehouse.copy(worker=worker, boxes=boxes).__str__()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# SOLVE
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def solve_weighted_sokoban(warehouse):
    '''
    This function analyses the given warehouse.
    It returns the two items. The first item is an action sequence solution. 
    The second item is the total cost of this action sequence.
    
    Solve Sokoban using A*


    @param 
     warehouse: a valid Warehouse object

    @return
    
        If puzzle cannot be solved 
            return 'Impossible', None
        
        If a solution was found, 
            return S, C 
            where S is a list of actions that solves
            the given puzzle coded with 'Left', 'Right', 'Up', 'Down'
            For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
            If the puzzle is already in a goal state, simply return []
            C is the total cost of the action sequence C

    '''
    
    taboo_str = taboo_cells(warehouse)
    taboo_set = set()
    walls = set(warehouse.walls)
    targets = set(warehouse.targets)
    interior = reachable(warehouse.worker, warehouse.boxes, walls)
    # taboo_cells returns a display string, we need to convert it to a set of coordinates
    for y, row in enumerate(taboo_str.split('\n')):
        for x, ch in enumerate(row):
            if ch == 'X':
                taboo_set.add((x, y))
 
    problem = SokobanPuzzle(warehouse, taboo_set)
    node = search.astar_graph_search(problem, h=problem.h)
 
    if node is None:
        return 'Impossible', None
 
    actions = node.solution()
    total_cost = node.path_cost
    return actions, total_cost
    


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import time
from sokoban import Warehouse

warehouses = [
    "warehouses/warehouse_09.txt",
    "warehouses/warehouse_07.txt",
    "warehouses/warehouse_47.txt",
    "warehouses/warehouse_81.txt",
    "warehouses/warehouse_147.txt",
]

for path in warehouses:
    wh = Warehouse()
    wh.load_warehouse(path)
    name = path.split("/")[-1]
    print(f"\n{'='*50}")
    print(f"Warehouse: {name}")
    print(f"Taboo cells:")
    print(taboo_cells(wh))
    print()
    t0 = time.time()
    actions, cost = solve_weighted_sokoban(wh)
    t1 = time.time()
    if actions == 'Impossible':
        print(f"{name:35s} | Impossible       | cost=None  | time={t1-t0:.2f}s")
    else:
        print(f"{name:35s} | {len(actions):2d} actions      | cost={cost:<6} | time={t1-t0:.2f}s")
        print(f"Moves: {actions}")