'''
File: plot.py
Authors: Logan Dihel
Date: 5/25/2018
Last Modified: 5/07/2025
Description: This module is a high-level interface
for manipulating and graphing netcdf4 files.
'''

import os
import re
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from datetime import datetime

class Plotter:
    def __init__(self, path, regexes=[r'.*?']):
        '''Load every file in a path that matches the regex.'''
        files = [os.path.join(path, x)
                 for x in os.listdir(path)
                 if any(re.match(pattern, x) for pattern in regexes)]

        if not files:
            print('No files found matching')
            return

        # Load all NetCDF files with xarray
        self.ds = xr.open_mfdataset(files, combine='by_coords')
        self.time = self.ds['time'].values.astype('datetime64[ns]').astype(datetime)

    def plot(self, *variable_groups, begin=None, end=None, width=18, height=6, hspace=0.4):
        if begin and end and begin >= end:
            print('Begin time must be before end time')
            return

        plot_groups = []
        variable_groups = [x if isinstance(x, list) else [x] for x in variable_groups]
        if not variable_groups:
            variable_groups = [['.*?']]

        for group in variable_groups:
            try:
                var_names = {x for pattern in group
                             for x in self.ds.variables.keys()
                             if re.search(pattern, x)}
            except:
                print('Incorrectly formatted regex in group:', group)
                continue

            shapes = {self.ds[x].shape for x in var_names}
            if len(shapes) != 1:
                for shape in shapes:
                    variable_groups.append(
                        ['^{}$'.format(x) for x in var_names if self.ds[x].shape == shape]
                    )
                continue

            dims = {self.ds[x].dims for x in var_names}
            if len(dims) != 1:
                for d in dims:
                    variable_groups.append(
                        ['^{}$'.format(x) for x in var_names if self.ds[x].dims == d]
                    )
                continue

            units = {self.ds[x].attrs.get('units', None) for x in var_names}
            if len(units) != 1:
                for u in units:
                    variable_groups.append(
                        ['^{}$'.format(x) for x in var_names if self.ds[x].attrs.get('units', None) == u]
                    )
                continue

            shape = list(shapes)[0]
            dimensions = len(shape)
            if dimensions == 0:
                plot_groups.append({'names': var_names, 'dimensions': [], 'slice': []})
            elif dimensions == 1:
                plot_groups.append({'names': var_names, 'dimensions': list(dims)[0], 'slice': [None]})
            elif dimensions == 2:
                for column in range(shape[1]):
                    plot_groups.append({
                        'names': var_names,
                        'dimensions': list(dims)[0],
                        'slice': [None, column]
                    })
            else:
                print('3D variables not supported yet.')

        if plot_groups:
            self._plot(plot_groups, begin, end, width, height, hspace)
        else:
            print('No variables to plot')

    def _plot(self, plot_groups, begin, end, width, height, hspace):
        num_plots = len(plot_groups)
        fig = plt.figure(figsize=(width, height * num_plots))
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

        start_index = bin_search(self.time, begin) if begin else 0
        end_index = bin_search(self.time, end) + 1 if end else self.time.size

        for i, group in enumerate(plot_groups):
            ax = fig.add_subplot(num_plots, 1, i + 1)
            var_names = group['names']
            dimensions = len(group['dimensions'])

            for j, var_name in enumerate(var_names):
                data = self.ds[var_name].values

                if dimensions == 0:
                    y = data
                    if is_numeric_array(y):
                        y = np.ma.masked_greater(y, 9e+36)
                    if y.size > 0:
                        ax.plot(y, marker='o', color=colors[j % len(colors)])

                elif dimensions == 1:
                    y = data[start_index:end_index]
                    if is_numeric_array(y):
                        y = np.ma.masked_greater(y, 9e+36)
                    if 'time' in group['dimensions']:
                        x = self.time[start_index:end_index]
                        ax.plot(x, y, marker='o', color=colors[j % len(colors)])
                    else:
                        ax.plot(y, marker='o', color=colors[j % len(colors)])

                elif dimensions == 2:
                    y = data[start_index:end_index, group['slice'][1]]
                    if is_numeric_array(y):
                        y = np.ma.masked_greater(y, 9e+36)
                    if 'time' in group['dimensions']:
                        x = self.time[start_index:end_index]
                        ax.plot(x, y, marker='o', color=colors[j % len(colors)])
                    else:
                        ax.plot(y, marker='o', color=colors[j % len(colors)])

            # X labels
            if dimensions == 0:
                ax.set_xlabel('data point')
            elif dimensions == 1:
                ax.set_xlabel(group['dimensions'][0])
            elif dimensions == 2:
                try:
                    dim1 = group['dimensions'][1]
                    val = self.ds[dim1].values[group['slice'][1]]
                    unit = self.ds[dim1].attrs.get('units', '')
                    ax.set_xlabel(f"{group['dimensions'][0]}, {dim1} ({val} {unit})")
                except:
                    ax.set_xlabel(f"{group['dimensions'][0]}, {group['dimensions'][1]} ({group['slice'][1]})")
            ax.set_title(', '.join(var_names))

            try:
                y_units = ', '.join({self.ds[x].attrs['units'] for x in var_names})
                ax.set_ylabel(y_units)
                ax.legend([f"{x} ({self.ds[x].attrs['units']})" for x in var_names])
            except:
                ax.set_ylabel('???')
                ax.legend([x for x in var_names])
            ax.grid()

        # plt.tight_layout()
        # plt.show()
        plt.subplots_adjust(hspace=hspace)  # Increase vertical space between plots
        plt.show()


# -------------------------------------------
# Helper Functions
# -------------------------------------------

def bin_search(a, d):
    '''Binary search helper for time slicing'''
    first = 0
    last = len(a) - 1
    m = -1

    while first <= last:
        m = (first + last) // 2
        if a[m] == d:
            return m
        elif a[m] > d:
            last = m - 1
        else:
            first = m + 1
    return m

def is_numeric_array(x):
    return np.issubdtype(x.dtype, np.number)