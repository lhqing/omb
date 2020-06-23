from ..App import dataset


N_CELLS = dataset.n_cells
N_REGION = dataset.get_variables('Region').unique().size
N_MAJOR_TYPE = dataset.get_variables('MajorType').unique().size

_subtypes = dataset.get_variables('SubType')
N_SUBTYPE = _subtypes[_subtypes.apply(lambda i: 'Outlier' not in i)].unique().size