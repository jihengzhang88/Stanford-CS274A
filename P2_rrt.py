import numpy as np
import matplotlib.pyplot as plt
from utils import plot_line_segments, line_line_intersection

class RRT(object):
    """ Represents a motion planning problem to be solved using the RRT algorithm"""
    def __init__(self, statespace_lo, statespace_hi, x_init, x_goal, obstacles):
        self.statespace_lo = np.array(statespace_lo)    # state space lower bound (e.g., [-5, -5])
        self.statespace_hi = np.array(statespace_hi)    # state space upper bound (e.g., [5, 5])
        self.x_init = np.array(x_init)                  # initial state
        self.x_goal = np.array(x_goal)                  # goal state
        self.obstacles = obstacles                      # obstacle set (line segments)
        self.path = None        # the final path as a list of states

    def is_free_motion(self, obstacles, x1, x2):
        """
        Subject to the robot dynamics, returns whether a point robot moving
        along the shortest path from x1 to x2 would collide with any obstacles
        (implemented as a "black box")

        Inputs:
            obstacles: list/np.array of line segments ("walls")
            x1: start state of motion
            x2: end state of motion
        Output:
            Boolean True/False
        """
        raise NotImplementedError("is_free_motion must be overriden by a subclass of RRT")

    def find_nearest(self, V, x):
        """
        Given a list of states V and a query state x, returns the index (row)
        of V such that the steering distance (subject to robot dynamics) from
        V[i] to x is minimized

        Inputs:
            V: list/np.array of states ("samples")
            x - query state
        Output:
            Integer index of nearest point in V to x
        """
        raise NotImplementedError("find_nearest must be overriden by a subclass of RRT")

    def steer_towards(self, x1, x2, eps):
        """
        Steers from x1 towards x2 along the shortest path (subject to robot
        dynamics). Returns x2 if the length of this shortest path is less than
        eps, otherwise returns the point at distance eps along the path from
        x1 to x2.

        Inputs:
            x1: start state
            x2: target state
            eps: maximum steering distance
        Output:
            State (numpy vector) resulting from bounded steering
        """
        raise NotImplementedError("steer_towards must be overriden by a subclass of RRT")

    def solve(self, eps, max_iters=1000, goal_bias=0.05, shortcut=False):
        """
        Constructs an RRT rooted at self.x_init with the aim of producing a
        dynamically-feasible and obstacle-free trajectory from self.x_init
        to self.x_goal.

        Inputs:
            eps: maximum steering distance
            max_iters: maximum number of RRT iterations (early termination
                is possible when a feasible solution is found)
            goal_bias: probability during each iteration of setting
                x_rand = self.x_goal (instead of uniformly randly sampling
                from the state space)
        Output:
            None officially (just plots), but see the "Intermediate Outputs"
            descriptions below
        """

        state_dim = len(self.x_init)

        # V stores the states that have been added to the RRT (pre-allocated at its maximum size
        # since numpy doesn't play that well with appending/extending)
        V = np.zeros((max_iters + 1, state_dim))
        V[0,:] = self.x_init    # RRT is rooted at self.x_init
        n = 1                   # the current size of the RRT (states accessible as V[range(n),:])

        # P stores the parent of each state in the RRT. P[0] = -1 since the root has no parent,
        # P[1] = 0 since the parent of the first additional state added to the RRT must have been
        # extended from the root, in general 0 <= P[i] < i for all i < n
        P = -np.ones(max_iters + 1, dtype=int)


        success = False

        ## Intermediate Outputs
        # You must update and/or populate:
        #    - V, P, n: the represention of the planning tree
        #    - success: whether or not you've found a solution within max_iters RRT iterations
        #    - self.path: if success is True, then must contain list of states (tree nodes)
        #          [x_init, ..., x_goal] such that the global trajectory made by linking steering
        #          trajectories connecting the states in order is obstacle-free.

        ## Hints:
        #   - use the helper functions find_nearest, steer_towards, and is_free_motion
        #   - remember that V and P always contain max_iters elements, but only the first n
        #     are meaningful! keep this in mind when using the helper functions!
        #   - the order in which you pass in arguments to steer_towards and is_free_motion is important

        ########## Code starts here ##########
        for i in range(max_iters):
            # Step 1: Sample a random point in the state space
            if np.random.rand() < goal_bias:
                x_rand = self.x_goal
            else:
                x_rand = np.random.uniform(self.statespace_lo, self.statespace_hi)

            # Step 2: Find nearest node in the tree
            nearest_idx = self.find_nearest(V[:n, :], x_rand)
            x_nearest = V[nearest_idx, :]

            # Step 3: Steer from x_nearest towards x_rand
            x_new = self.steer_towards(x_nearest, x_rand, eps)

            # Step 4: Check if motion from x_nearest to x_new is free
            if self.is_free_motion(self.obstacles, x_nearest, x_new):
                # Step 5: Add the new node to the tree
                V[n, :] = x_new
                P[n] = nearest_idx
                n += 1

                # Step 6: Check if the new node is close to the goal
                if np.linalg.norm(x_new - self.x_goal) < eps:
                    success = True
                    break
        
        if success:
            # Reconstruct the path from x_goal back to x_init
            self.path = [self.x_goal]
            current_idx = n - 1
            while current_idx != 0:
                self.path.append(V[current_idx])
                current_idx = P[current_idx]
            self.path.append(self.x_init)
            self.path.reverse()  # Reverse the path to go from x_init to x_goal

            # Apply shortcutting if enabled
            if shortcut:
                self.shortcut_path()
            ########## Code ends here ##########

        plt.figure()
        self.plot_problem()
        self.plot_tree(V, P, color="blue", linewidth=.5, label="RRT tree", alpha=0.5)
        if success:
            if shortcut:
                self.plot_path(color="purple", linewidth=2, label="Original solution path")
                self.shortcut_path()
                self.plot_path(color="green", linewidth=2, label="Shortcut solution path")
            else:
                self.plot_path(color="green", linewidth=2, label="Solution path")
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.03), fancybox=True, ncol=3)
            plt.scatter(V[:n,0], V[:n,1])
        else:
            print("Solution not found!")

        return success

    def plot_problem(self):
        plot_line_segments(self.obstacles, color="red", linewidth=2, label="obstacles")
        plt.scatter([self.x_init[0], self.x_goal[0]], [self.x_init[1], self.x_goal[1]], color="green", s=30, zorder=10)
        plt.annotate(r"$x_{init}$", self.x_init[:2] + [.2, 0], fontsize=16)
        plt.annotate(r"$x_{goal}$", self.x_goal[:2] + [.2, 0], fontsize=16)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.03), fancybox=True, ncol=3)
        plt.axis('scaled')

    def shortcut_path(self):
        """
        Iteratively removes nodes from solution path to find a shorter path
        which is still collision-free.
        Input:
            None
        Output:
            None, but should modify self.path
        """
        ########## Code starts here ##########
        if self.path is None or len(self.path) < 3:
            # No shortcutting is possible if there are fewer than 3 nodes (x_init, intermediate nodes, x_goal)
            return

        success = False

        while not success:
            success = True  # Assume success until proven otherwise
            # Iterate over the path, skipping the first and last nodes
            i = 1
            while i < len(self.path) - 1:
                parent_node = self.path[i - 1]  # PARENT(x)
                current_node = self.path[i]     # x
                child_node = self.path[i + 1]   # CHILD(x)

                # Check if we can connect the parent and the child directly
                if self.is_free_motion(self.obstacles, parent_node, child_node):
                    # Remove the current node since it's unnecessary
                    self.path.pop(i)
                    success = False  # Need to continue since we modified the path
                else:
                    # Move to the next node
                    i += 1
        ########## Code ends here ##########

class GeometricRRT(RRT):
    """
    Represents a geometric planning problem, where the steering solution
    between two points is a straight line (Euclidean metric)
    """

    def find_nearest(self, V, x):
        # Consult function specification in parent (RRT) class.
        ########## Code starts here ##########
        # Hint: This should take 1-3 line.
        # Compute Euclidean distance to all points in V
        distances = np.linalg.norm(V[:len(V)] - x, axis=1)
        # Return the index of the minimum distance
        return np.argmin(distances)
        ########## Code ends here ##########

    def steer_towards(self, x1, x2, eps):
        # Consult function specification in parent (RRT) class.
        ########## Code starts here ##########
        # Hint: This should take 1-4 line.
        # Compute the distance between x1 and x2
        dist = np.linalg.norm(x2 - x1)
        
        # If distance is less than eps, return x2
        if dist <= eps:
            return x2
        
        # Otherwise, return a point along the line at distance eps from x1
        direction = (x2 - x1) / dist  # Unit vector from x1 to x2
        return x1 + eps * direction
        ########## Code ends here ##########


    def is_free_motion(self, obstacles, x1, x2):
        motion = np.array([x1, x2])
        for line in obstacles:
            if line_line_intersection(motion, line):
                return False
        return True

    def plot_tree(self, V, P, **kwargs):
        plot_line_segments([(V[P[i],:], V[i,:]) for i in range(V.shape[0]) if P[i] >= 0], **kwargs)

    def plot_path(self, **kwargs):
        if self.path is None or len(self.path) == 0:
            print("No path found!")
            return
        path = np.array(self.path)
        plt.plot(path[:,0], path[:,1], **kwargs)
