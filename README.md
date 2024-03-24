# XfoilParsecOptimizer

### Introduction
This project aims to provide an efficent, easy-to-use and easy-to-understand toolbox for PARSEC encoded airfoil optimization in python using [Xfoil](https://web.mit.edu/drela/Public/web/xfoil/). All modules are written in pure numpy, and laverage numpy's [np.vectorize](https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html) function, accelerating calculations significantly. The structure of the project is kept as simple as possible. Between the modules, there are no cross-dependencies, allowing you to easily integrate and extend this project into your own work.

### Getting Started
A utility script `install_xfoil.sh` for setting up XFOIL in `/bin` on any Ubuntu-based distribution is provided. This script can easily be adjusted to any UNIX-System. The script is based on [XFOIL-Compilation](https://github.com/christophe-david/XFOIL_compilation).

After installing Xfoil, there are only 3 required modules, that empower you as a user to easily and efficiently perform PARSEC-encoded airfoil optimization:

1. generate_airfoils.py: Given a PARSEC expression, this function generates a customizable amount of `N_XY_COORDINATES`. An interface for checking the validity of these designs *before* evaluation is provided. Invalidity resulting from undesirable airfoils, such as (a) intersecting polynomials (b) multiple local maxima on the upper polynomial (c) negative y coordinates on the upper polynomial is already implemented. This gives you the ability to filter bad designs before wasting valuable CPU time on evaluation. By default, this module then writes the coordinates of valid airfoils in Xfoil-compatible format into `f'airfoil_{index}.dat'`. This behavior can be deactived by setting the `io_flag` to false, allowing you to accelerate calculation, whenever you want to filter invalid designs during your own optimization process.
2. simulate_airfoils.py: Evaluates a specified amount of `f'airfoil_{index}.dat'`-files using Xfoil. The code is structured in a parallelizable manner. Unfortunately, I have yet not achieved to completely achieve parallelization.
3. eval_xfoil_loop.py: Serves as a wrapper module for the beforementioned modules. Within a vectorized for-loop it (1) generates airfoils, (2) simulates them, (3) returns the objective values, convergence errors, and successful evaluations. Rather than being seen as an exemplary use-case, that can be adjusted to your needs.

### PARSEC Encoding Format
This project uses encoding, as done in [SAIL](https://arxiv.org/pdf/1806.05865).

#INCLUDEGRAPHIC

`generate_airfoils(parsec_airfoils)` expects PARSEC-vectors in the following format:

`PARSEC_AIRFOILS=[rLeUp, Xup, Zup, Z_XXup, rLeLo, Xlo, Zlo, Z_XXlo, dZ_Te, Z_Te, a_Te, b_Te]`

The value ranges below have proven to work well for me. If you are unsure, what value ranges you need to use for PARSEC encoding, you can simply use these. (taken from [here](https://github.com/agaier/sail/blob/master/domains/parsec/airFoilTools/encoding/expressParsec.m))
```
EXAMPLATORY_VALUE_RANGE = [
    ( 0.00375 , 0.0500), # 1 rLeUp:    leading edge radius upper curve
    ( 0.26250 , 0.6875), # 2 Xup:      location of highest point (x coord)
    ( 0.07250 , 0.1875), # 3 Zup:      location of highest point (z coord)
    (-0.75000 , 0.2500), # 4 Z_XXup:   upper curvature    
    ( 0.00500 , 0.0400), # 5 rLeLo:    leading edge radius lower curve
    ( 0.30000 , 0.6000), # 6 Xlo       location of lowest point  (x coord)
    (-0.05875 ,-0.0120), # 7 Zlo:      location of lowest point  (z coord)
    (-0.81000 ,-0.3750), # 8 Z_XXlo:   lower curvature
    (   0.001 ,  0.001), # 9 dZ_Te     distance trailing edge
    (-0.00000 , 0.0100), # 10 Z_Te     Z position of trailing edge
    (-6.00000 ,-2.0125), # 11 a Te     upper trailing edge angle (degrees)
    ( 2.50000 ,11.413)]  # 12 b_Te     lower trailing edge agnle (degrees)
```

### Contributing
Up to the date, other repositories exist, however, I have perceived them hard to understand, and inefficient for optimization purposes, which require tens of thousands of evaluations. I have used this code to generate and evaluate large numbers of airfoils in relatively short time. Still, this project is not optimal, and there is still many things, that can be improved. If you have any suggestions for this project, feel free to open an issue or pull request :)
