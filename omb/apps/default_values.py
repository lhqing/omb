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