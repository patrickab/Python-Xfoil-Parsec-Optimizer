"""
Levarges numpy.vectorize inside generate_parsec_coordinates for faster calculation
Ensures that i_solutions <= BATCH_SIZE are evaluated.

Allows vectorized evaluation for any amount n=solution_batch.size[0]

    - Allows indices eg [20:22] to be evaluated, if 2 samples are left
"""

import numpy as np

### Custom Scripts ###
from generate_airfoils import generate_parsec_coordinates
from simulate_airfoils import xfoil

### Global Parameters ###
BATCH_SIZE = 10

def eval_xfoil_loop(solution_batch):

    n_errors = 0
    objective_batch = np.empty((0, 1))

    # enter batch parallel for loop for vectorized parallelization
    for i in range(0, solution_batch.shape[0], BATCH_SIZE):

        i_solutions = solution_batch[i:i+BATCH_SIZE]
        i_solutions = np.vstack(i_solutions)

        # generates coordinate files in the working directory
        generate_parsec_coordinates(i_solutions)

        # evalutes previously generated coordinate files on custom objective function
        #     obj = -log(drag/lift)
        _, success_indices, converged_obj = xfoil(i_solutions.shape)

        if len(success_indices) == 0:
            # if no solution converges, skip to next iteration
            continue

        success_indices = success_indices[:i_solutions.shape]
        converged_sol = i_solutions[success_indices]

        i_errors = i_solutions.shape - len(success_indices)
        n_errors += i_errors

        objective_batch = np.vstack((objective_batch, np.vstack(converged_sol))) if objective_batch.shape[0] != 0 else np.vstack(converged_sol)

    return objective_batch, n_errors
