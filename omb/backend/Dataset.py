"""
Design:
Dataset contain everything related to the apps, provides api that's used by dash apps
Dataset load cell coords, user provided variables, and palettes into memory, assuming they are not large.
Dataset load gene or other large data lazily from xarray netCDF file, with lru_cache
Dataset only has "getter" but not "setter", TODO let's think about front-end user provided custom info later.
"""
import pathlib

import pandas as pd

from .ingest import DATASET_DIR, COORDS_PATH, CELL_ID_PATH, VARIABLE_PATH, PALETTE_PATH
from .utilities import *


def _validate_dataset_dir():
    has_error = False
    for path in [DATASET_DIR, COORDS_PATH, CELL_ID_PATH, VARIABLE_PATH, PALETTE_PATH]:
        try:
            assert pathlib.Path(path).exists()
        except AssertionError:
            print(f'Dataset related path: {path} do not exist')
            has_error = True
    if has_error:
        raise FileNotFoundError('The dataset dir may be incomplete, cause some file path not found.')
    return


class Dataset:
    def __init__(self, dataset_dir=DATASET_DIR):
        # validate all paths
        _validate_dataset_dir()
        self.dataset_dir = pathlib.Path(dataset_dir)

        # load cell coords
        with pd.HDFStore(self.dataset_dir / COORDS_PATH) as hdf:
            coord_dict = {k.lstrip('/'): hdf[k] for k in hdf.keys()}
        self._coord_dict = coord_dict
        self.coord_names = list(coord_dict.keys())

        # load cell ids
        self._cell_id_to_int = read_msgpack(self.dataset_dir / CELL_ID_PATH)
        self._int_to_cell_id = {v: k for k, v in self._cell_id_to_int.items()}
        self.n_cells = len(self._cell_id_to_int)

        # load cell tidy table
        self._variables = pd.read_hdf(self.dataset_dir / VARIABLE_PATH, key='data')
        # Categorical var
        self.categorical_var = self._variables.columns[self._variables.dtypes == 'category'].tolist()
        self.n_categorical_var = len(self.categorical_var)
        # Continuous var
        self.continuous_var = self._variables.columns[self._variables.dtypes != 'category'].tolist()
        self.n_continuous_var = len(self.continuous_var)

        # load palette for Categorical var
        self._palette = read_msgpack(self.dataset_dir / PALETTE_PATH)

        print(self.categorical_var)
        print(self.continuous_var)

        return

    def get_coords(self, name):
        return self._coord_dict[name].copy()

    def get_palette(self, name):
        return self._palette[name]

    def get_variables(self, name):
        return self._variables[name].copy()
