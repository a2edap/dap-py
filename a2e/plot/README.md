# a2e.plot Package

This package contains the plot module. The package requires matplotlib, numpy, and xarray as dependencies, in addition to the standard Python core libraries.

## plot Module


This module is useful for plotting different variables against each other using matplotlib in just one line of code. It is designed for users who want a quick way to visualize their NetCDF data and run simple analyses.

The module supports NetCDF-4 files (including compression and groups) using the xarray interface.

## Setup

First, import the module. If using Jupyter Notebook, be sure to use the iPython magic `%` to setup matplotlib:

```python
%matplotlib inline
from a2e.plot import plot
```

Next, create a Plotter object:

```python
plotter = plot.Plotter('/var/tmp/wfip2.lidar.z01.b0/')
```

And that's it. Create plots using the `plot` function.

### Plotting

After setting up the plotter, just call the `plot` function. The function signature is provided here:

#### `plotter.plot(*variable_groups, begin=None, end=None, width=18, height=6)`

The plot method is intelligent and will group variables based on its shape, dimension, and units. The user can specify which variables to plot against one another over an optional time frame.

##### `variable_groups`

Pass in regular expressions for the plotter to generate the corresponding plots. For variables that should be plotted against one another, group their regular expressions into lists (_not tuples!_). The regular expressions are evaluated with the `re.search()` function which behaves similar to regular expressions in Perl as matches can be found in the middle of a word rather than just at the beginning. If no `variable_groups` are specified, the function defaults to using `.*?` which plots every variable.

##### `begin`

Datetime object specifying the beginning of the plot.

##### `end`

Datetime object specifying the end of the plot.

##### `width`

Width of each plot in inches.

##### `height`

Height of each plot in inches.

##### `hspace`

Vertical spacing between subplots. Default is `0.4`.
  
## Example

```python
%matplotlib inline
from a2e.plot import plot

plotter = plot.Plotter('/var/tmp/wfip2.lidar.z01.b0/')

# plots wind_u, wind_v, and vertical_air_velocity
# against each other, while height and time variables
# are plotted by themselves
plotter.plot(
    ['wind_[uv]$', '^vertical_air_velocity$'],
    '^height$',
    'time$',
)
```