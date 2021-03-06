"""
Ingest user input data to standard internal Dataset, so everything after ingest is automatic

Several main things
# Coords file
- The name of the file before first "." char will be the name of the coords set.
- No header
- First column must be cell id
- Second (x), third (y), and forth (z, optional) column are coordinates
- Each file only contain one set of coordinates, if have multiple views, use multiple coords files.
- Coords transfer into np.float16

# Categorical / Continuous variables
- Header according to variable name
- First column must be cell id, all cell ids must exist in the coords
- Columns may have nan

# Palette
- Int id map to real str id
- Associated with continuous variable, categorical variable, and region values

# Gene

"""
import pathlib
import warnings

import numpy as np
import pandas as pd

import omb
from .utilities import *

"""
File names in ingested dataset dir
"""
DATASET_DIR = f'{omb.__path__[0]}/Data/Dataset/'
COORDS_PATH = f'{DATASET_DIR}/Coords.h5'
COORDS_CELL_TYPE_PATH = f'{DATASET_DIR}/CellTypeOccurInCoords.lib'
CELL_ID_PATH = f'{DATASET_DIR}/CellIDMap.msg'
VARIABLE_PATH = f'{DATASET_DIR}/Variables.h5'
PALETTE_PATH = f'{DATASET_DIR}/Palette.json'
BRAIN_REGION_PATH = f'{DATASET_DIR}/BrainRegion.csv'
CELL_TYPE_PATH = f'{DATASET_DIR}/CellType.csv'
GENE_META_PATH = f'{DATASET_DIR}/GeneMeta.h5'
GENE_TO_MCDS_PATH = f'{DATASET_DIR}/GeneToMCDSName.json'  # int to name of the MCDS chunk that contain this gene

GENE_MCDS_DIR = '/home/hanliu/project/cemba/gene_rate_for_browser/CEMBA_45_Region'
if not pathlib.Path(GENE_MCDS_DIR).exists():
    # neomorph location
    GENE_MCDS_DIR = '/home/hanliu/gene_rate_for_app/CEMBA_RS1_45Region'

# pairwise DMG
PAIRWISE_DMG_DIR = '/home/hanliu/project/cemba/gene_rate_for_browser/pairwise_dmg'
if not pathlib.Path(PAIRWISE_DMG_DIR).exists():
    # neomorph location
    PAIRWISE_DMG_DIR = '/home/hanliu/gene_rate_for_app/pairwise_dmg'
CLUSTER_DIST_PATH = f'{PAIRWISE_DMG_DIR}/ClusterDistance.h5'
TOTAL_PAIRWISE_DMG_PATH = f'{PAIRWISE_DMG_DIR}/TotalPairwiseDMG.h5'
PROTEIN_CODING_PAIRWISE_DMG_PATH = f'{PAIRWISE_DMG_DIR}/ProteinCodingPairwiseDMG.h5'

# AnnoJ
ANNOJ_META_PATH = f'{DATASET_DIR}/AnnoJMeta.csv'
ANNOJ_URL_BASE = 'http://neomorph.salk.edu/mouse_brain.php'

# Allen CCF metadata
ALLEN_CCF_META_PATH = f'{DATASET_DIR}/allen_ccf_meta.csv'
ALLEN_CCF_ACRONYM_TO_NAME = f'{DATASET_DIR}/acronym_to_name.json'
CEMBA_ACRONYM_TO_NAME = f'{DATASET_DIR}/acronym_to_name.cemba_region.json'

"""
Default data types
"""
COORDS_DTYPE = np.float16
CONTINUOUS_VAR_DTYPE = np.float32


def ingest_cell_coords(coords_dir):
    """
    Load all the coords, use union of cell ids and map all cell id into int internally, return the cell map dict.
    Parameters
    ----------
    coords_dir
        User input dir path
    Returns
    -------
    cell_to_int: dict
        cell to int map, use for all other data's cell id validation and conversion
    """
    # load all the coords
    print(f'Loading cell coords')
    coords_dict = {}
    for path in list(coords_dir.glob('*csv.gz')):
        coord_name = path.name.split('.')[0]
        coords_df = pd.read_csv(path, header=None, index_col=0).astype(COORDS_DTYPE)
        coords_df.index.name = 'cell'
        if coords_df.shape[1] == 2:
            coords_df.columns = ['x', 'y']
        elif coords_df.shape[1] == 3:
            coords_df.columns = ['x', 'y', 'z']
        else:
            raise NotImplementedError(f'Coords table right now only support 2D or 3D, '
                                      f'got a table with {coords_df.shape[1]} dims.')
        coords_dict[coord_name] = coords_df

    # generate cell_id map
    total_cell_ids = set()
    for k, v in coords_dict.items():
        total_cell_ids |= set(v.index)
    cell_to_int = {c: i for i, c in enumerate(total_cell_ids)}
    del total_cell_ids
    print(f'Got a total of {len(cell_to_int)} unique cell ids from all coords files')

    # change all the coords table index into int
    print(f'Standardizing internal cell ids')
    for k, v in coords_dict.items():
        v.index = v.index.map(cell_to_int)

    print(f'Saving coords and cell ids')
    with pd.HDFStore(COORDS_PATH, 'w') as hdf:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for k, v in coords_dict.items():
                hdf[k] = v
    write_msgpack(CELL_ID_PATH, cell_to_int)

    return cell_to_int


def ingest_variables(cell_to_int, categorical_path=None, continuous_path=None):
    variables_to_cat = []

    if categorical_path is not None:
        # TODO change to csv
        categorical_df = pd.read_hdf(categorical_path, key='data').astype('category')
        # validate cell ids before conversion
        cell_not_in_coords = categorical_df.index[~categorical_df.index.isin(cell_to_int)]
        error_str = ', '.join(cell_not_in_coords[:10])
        try:
            assert cell_not_in_coords.size == 0
        except AssertionError:
            raise KeyError(f'{cell_not_in_coords.size} cell ids found in categorical variable table '
                           f'do not found in any coords table, e.g. {error_str}')
        else:
            categorical_df.index = categorical_df.index.map(cell_to_int)
            cells, num_vars = categorical_df.shape
            print(f'Got {num_vars} categorical variables for {cells} cells.')
            variables_to_cat.append(categorical_df)

    if continuous_path is not None:
        # TODO change to csv
        continuous_df = pd.read_hdf(continuous_path, key='data').astype(CONTINUOUS_VAR_DTYPE)
        # validate cell ids before conversion
        cell_not_in_coords = continuous_df.index[~continuous_df.index.isin(cell_to_int)]
        error_str = ', '.join(cell_not_in_coords[:10])
        try:
            assert cell_not_in_coords.size == 0
        except AssertionError:
            raise KeyError(f'{cell_not_in_coords.size} cell ids found in continuous variable table '
                           f'do not found in any coords table, e.g. {error_str}')
        else:
            continuous_df.index = continuous_df.index.map(cell_to_int)
            cells, num_vars = continuous_df.shape
            print(f'Got {num_vars} continuous variables for {cells} cells.')
            variables_to_cat.append(continuous_df)

    if len(variables_to_cat) != 0:
        total_variables = pd.concat(variables_to_cat, axis=1, sort=True)
    else:
        total_variables = pd.DataFrame([], index=cell_to_int.values())

    total_variables.to_hdf(VARIABLE_PATH, key='data', format="table")
    return total_variables


def ingest_palette(total_variables, palette_path=None):
    if palette_path is not None:
        # TODO change to json
        palette = read_msgpack(palette_path)

        categorical_variables = total_variables.select_dtypes('category')

        for k, _ in palette.items():
            try:
                cate_data = categorical_variables[k]
            except KeyError:
                raise KeyError(f'{k} is not provided as a categorical variable, but exist in palette.')

            # TODO check if cate_data completely exist in palette?
            # TODO check values is hex? Standardize the color to certain format?
    else:
        # make an empty palette anyway, prevent file not found
        palette = {}

    write_msgpack(PALETTE_PATH, palette)
    return


def ingest_genes():
    # TODO
    return


if __name__ == '__main__':
    # TODO add test here
    pass
