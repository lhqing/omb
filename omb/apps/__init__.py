"""
in-memory dataset is loaded from init
"""
from .brain_region_browser import create_brain_region_browser_layout
from .cell_type_browser import create_cell_type_browser_layout
from .gene_browser import create_gene_browser_layout
from .home import layout as home_layout
from .paired_scatter_browser import create_paired_scatter_layout, paired_scatter_api
from .brain_region_table import create_brain_table_layout
from .cell_type_table import create_cell_type_table_layout
from .cell_type_dmr_browser import create_cell_type_dmr_layout
