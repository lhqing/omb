"""
Design:
Dataset contain everything related to the apps, provides api that's used by dash apps
Dataset load cell coords, user provided variables, and palettes into memory, assuming they are not large.
Dataset load gene or other large data lazily from xarray netCDF file, with lru_cache
Dataset only has "getter" but not "setter", TODO let's think about front-end user provided custom info later.
"""
import json
import pathlib
import xarray as xr
import pandas as pd
from functools import lru_cache
from .ingest import \
    DATASET_DIR, \
    COORDS_PATH, \
    CELL_ID_PATH, \
    VARIABLE_PATH, \
    PALETTE_PATH, \
    BRAIN_REGION_PATH, \
    CELL_TYPE_PATH, \
    GENE_MCDS_DIR, \
    GENE_META_PATH, \
    GENE_TO_MCDS_PATH
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

        # separate table for region and cluster annotation
        # brain region table, index is Region Name
        self._brain_region_table = pd.read_csv(BRAIN_REGION_PATH, index_col=0)
        self.dissection_regions = self._brain_region_table.index.tolist()
        self.major_regions = list(self._brain_region_table['Major Region'].unique())
        self.sub_regions = list(self._brain_region_table['Sub-Region'].unique())

        self.dissection_region_to_major_region = self._brain_region_table['Major Region'].to_dict()
        self.dissection_region_to_sub_region = self._brain_region_table['Sub-Region'].to_dict()

        # cell type maps
        self._cell_type_table = pd.read_csv(CELL_TYPE_PATH, index_col=0)
        self.sub_type_to_major_type = self._variables.set_index('SubType')['MajorType'].to_dict()
        self.sub_type_to_cell_class = self._variables.set_index('SubType')['CellClass'].to_dict()

        # gene rate
        self._gene_meta_table = pd.read_csv(GENE_META_PATH, index_col=0)  # index is gene int gene_id is a column
        self._gene_id_to_int = {v: k for k, v in self._gene_meta_table['gene_id'].items()}
        # TODO gene name is not unique
        self._gene_name_to_int = {v: k for k, v in self._gene_meta_table['gene_name'].items()}

        with open(GENE_TO_MCDS_PATH) as f:
            gene_to_mcds_name = json.load(f)
            self._gene_to_mcds_path = {g: f'{GENE_MCDS_DIR}/{n}' for g, n in gene_to_mcds_name.items()}

        print('dataset.categorical_var', self.categorical_var)
        print('dataset.continuous_var', self.continuous_var)

        return

    def get_coords(self, name):
        return self._coord_dict[name].copy()

    def get_palette(self, name):
        return self._palette[name]

    def get_variables(self, name):
        return self._variables[name].copy()

    @lru_cache(maxsize=256)
    def get_gene_rate(self, gene, mc_type='CHN'):
        if gene.startswith('ENSMUSG'):
            gene_int = self._gene_id_to_int[gene]
        else:
            gene_int = self._gene_name_to_int[gene]
        mcds_path = self._gene_to_mcds_path[gene_int]

        # it took 250ms to get a gene value series for 100k cell
        # because MCDS is re chunked and saved based on gene chunks rather than cell chunk
        # see prepare_gene_rate_for_browser.ipynb
        data = xr.open_dataset(mcds_path)['gene_da'].sel(gene=gene_int, mc_type=mc_type).to_pandas()
        return data

    @property
    def brain_region_table(self):
        return self._brain_region_table.copy()

    @property
    def cell_type_table(self):
        return self._cell_type_table.copy()

    @property
    def gene_meta_table(self):
        return self._gene_meta_table.copy()

    @property
    def region_label_to_dissection_region_dict(self):
        total_dict = {'ALL REGIONS': self._brain_region_table.index.tolist()}
        for major_region, sub_df in self._brain_region_table.groupby('Major Region'):
            total_dict[major_region] = sub_df.index.tolist()
        for sub_region, sub_df in self._brain_region_table.groupby('Sub-Region'):
            total_dict[sub_region] = sub_df.index.tolist()
        for region in self.dissection_regions:
            total_dict[region] = [region]
        return total_dict
