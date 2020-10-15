from ..backend import dataset

N_CELLS = dataset.n_cells
N_REGION = dataset.get_variables('Region').unique().size
N_MAJOR_TYPE = dataset.get_variables('MajorType').unique().size

_subtypes = dataset.get_variables('SubType')
N_SUBTYPE = _subtypes[_subtypes.apply(lambda i: 'Outlier' not in i)].unique().size

DEFAULT_BRAIN_REGION_IMG_SRC = \
    f'https://raw.githubusercontent.com/lhqing/omb/master/omb/assets/dissection_region_img/brain_region_demo.jpg'
BRAIN_REGION_IMG_PATTERN = 'https://raw.githubusercontent.com/lhqing/omb/master/' \
                           'omb/assets/dissection_region_img/{dissection_region}.jpeg'

CELL_TYPE_LEVELS = ['CellClass', 'MajorType', 'SubType']
REGION_LEVELS = ['MajorRegion', 'SubRegion', 'RegionName']

DOWN_SAMPLE = 10000

GENE_META_DF = dataset.gene_meta_table
MAX_TRACKS = 12
CATEGORICAL_VAR = [
    'RegionName', 'MajorRegion', 'SubRegion', 'CellClass', 'MajorType',
    'SubType'
]

CONTINUOUS_VAR = [
    'CCC_Rate', 'CG_Rate', 'CG_RateAdj', 'CH_Rate', 'CH_RateAdj',
    'FinalReads', 'InputReads', 'MappedReads', 'BamFilteringRate',
    'MappingRate', 'Slice'
]

CONTINUOUS_VAR_NORMS = {
    'CCC_Rate': (0, 0.03),
    'CG_Rate': (0.65, 0.85),
    'CG_RateAdj': (0.65, 0.85),
    'CH_Rate': (0, 0.04),
    'CH_RateAdj': (0, 0.04),
    'FinalReads': (5e5, 2e6),
    'InputReads': (1e6, 5e6),
    'MappedReads': (5e5, 3e6),
    'BamFilteringRate': (0.5, 0.8),
    'MappingRate': (0.5, 0.8)
}

VAR_NAME_MAP = {
    'RegionName': 'Dissection Region',
    'MajorRegion': 'Major Region',
    'SubRegion': 'Sub-region',
    'CellClass': 'Cell Class',
    'MajorType': 'Major Type',
    'SubType': 'Subtype',
    'CCC_Rate': 'mCCC Fraction',
    'CG_Rate': 'mCG Fraction',
    'CH_Rate': 'mCG Fraction',
    'CG_RateAdj': 'Adj. mCG Fraction',
    'CH_RateAdj': 'Adj. mCG Fraction',
    'FinalReads': 'Final Reads',
    'InputReads': 'Input Reads',
    'MappedReads': 'Mapped Reads',
    'BamFilteringRate': 'BAM Filtering Rate',
    'MappingRate': 'Mapping Rate',
    'Slice': 'Brain Slice'
}
