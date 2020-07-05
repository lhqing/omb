"""
Design:
Dataset contain everything related to the apps, provides api that's used by dash apps
Dataset load cell coords, user provided variables, and palettes into memory, assuming they are not large.
Dataset load gene or other large data lazily from xarray netCDF file, with lru_cache
Dataset only has "getter" but not "setter", TODO let's think about front-end user provided custom info later.
"""
import json
import pathlib
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import xarray as xr

from .ingest import \
    DATASET_DIR, \
    COORDS_PATH, \
    COORDS_CELL_TYPE_PATH, \
    CELL_ID_PATH, \
    VARIABLE_PATH, \
    PALETTE_PATH, \
    BRAIN_REGION_PATH, \
    CELL_TYPE_PATH, \
    GENE_MCDS_DIR, \
    GENE_META_PATH, \
    GENE_TO_MCDS_PATH, \
    CLUSTER_DIST_PATH, \
    TOTAL_PAIRWISE_DMG_PATH, \
    PROTEIN_CODING_PAIRWISE_DMG_PATH, \
    ANNOJ_META_PATH, \
    ANNOJ_URL_BASE
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
        # key is coord name, value is cell type list that occur in this coord
        self.coord_cell_type_occur = joblib.load(COORDS_CELL_TYPE_PATH)

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

        # separate table for region and cluster annotation
        # brain region table, index is Region Name
        self._brain_region_table = pd.read_csv(BRAIN_REGION_PATH, index_col=0)
        self.dissection_regions = self._brain_region_table.index.tolist()
        self.major_regions = list(self._brain_region_table['Major Region'].unique())
        self.sub_regions = list(self._brain_region_table['Sub-Region'].unique())
        self.region_label_to_cemba_name = self._brain_region_table['Dissection Region ID'].to_dict()
        self.cemba_name_to_region_label = {v: k for k, v in self.region_label_to_cemba_name.items()}
        self.dissection_region_to_major_region = self._brain_region_table['Major Region'].to_dict()
        self.dissection_region_to_sub_region = self._brain_region_table['Sub-Region'].to_dict()

        # cell type maps
        self._cell_type_table = pd.read_csv(CELL_TYPE_PATH, index_col=0)
        self.child_to_parent = self._cell_type_table.loc[
            self._cell_type_table['Cluster Level'] == 'SubType', 'Parent'].to_dict()
        self.child_to_parent.update(self._cell_type_table.loc[
                                        self._cell_type_table['Cluster Level'] == 'MajorType', 'Parent'].to_dict())
        self.sub_type_to_cell_class = self._variables.set_index('SubType')['CellClass'].to_dict()
        self.parent_to_children_list = self._cell_type_table.groupby('Parent').apply(
            lambda i: i.index.tolist()).to_dict()
        self.cluster_name_to_level = self._cell_type_table['Cluster Level'].to_dict()

        # load palette for Categorical var
        self._palette = read_msgpack(self.dataset_dir / PALETTE_PATH)
        self._palette['RegionName'] = {self.cemba_name_to_region_label[k]: v
                                       for k, v in self._palette['Region'].items()}

        # gene rate
        self._gene_meta_table = pd.read_csv(GENE_META_PATH, index_col=0)  # index is gene int gene_id is a column
        self.gene_id_to_int = {v: k for k, v in self._gene_meta_table['gene_id'].items()}
        # TODO gene name is not unique
        self.gene_name_to_int = {v: k for k, v in self._gene_meta_table['gene_name'].items()}

        with open(GENE_TO_MCDS_PATH) as f:
            gene_to_mcds_name = json.load(f)
            self._gene_to_mcds_path = {int(g): f'{GENE_MCDS_DIR}/{n}' for g, n in gene_to_mcds_name.items()}

        # Pairwise DMG
        self._cluster_dist = pd.read_hdf(CLUSTER_DIST_PATH)

        # AnnoJ metadata
        self._annoj_track_meta = pd.read_csv(ANNOJ_META_PATH, index_col=0)
        self._annoj_gene_track_id = self._annoj_track_meta.loc['Gene', 'id']
        self._subtype_to_annoj_track_id = self._annoj_track_meta[self._annoj_track_meta['type'] == 'MethTrack'][
            'id'].to_dict()

        # print('dataset.categorical_var', self.categorical_var)
        # print('dataset.continuous_var', self.continuous_var)

        return

    def get_coords(self, name):
        return self._coord_dict[name].copy()

    def get_palette(self, name):
        return self._palette[name]

    def get_variables(self, name):
        return self._variables[name].copy()

    @lru_cache(maxsize=256)
    def get_gene_rate(self, gene, mc_type='CHN'):
        if isinstance(gene, int):
            gene_int = gene
        elif gene.startswith('ENSMUSG'):
            gene_int = self._gene_id_to_int[gene]
        else:
            gene_int = self._gene_name_to_int[gene]
        mcds_path = self._gene_to_mcds_path[gene_int]

        # it took 250ms to get a gene value series for 100k cell
        # because MCDS is re chunked and saved based on gene chunks rather than cell chunk
        # see prepare_gene_rate_for_browser.ipynb
        data = xr.open_dataset(mcds_path)['gene_da'].sel(gene=gene_int, mc_type=mc_type).to_pandas()

        # return np.float16 to reduce data transfer
        return data.astype(np.float16)

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

    def query_dmg(self, hypo_clusters, hyper_clusters, cluster_level, top_n=100, protein_coding=True):
        """
        Given two set of clusters in the same level, order CH DMGs and return a gene meta table

        Parameters
        ----------
        hypo_clusters
            List of cluster names, need to be the same level
        hyper_clusters
            List of cluster names, need to be the same level
        cluster_level
            CellClass, Subtype or MajorType
        top_n
            Top N genes to return, the actual number <= top_n
        protein_coding
            If True, only return protein coding genes
        Returns
        -------
        Ranked DMG metadata table
        """

        if protein_coding:
            hdf_path = PROTEIN_CODING_PAIRWISE_DMG_PATH
        else:
            hdf_path = TOTAL_PAIRWISE_DMG_PATH

        # rank gene based on all possible pair AUROC weighted by
        records = {}
        with pd.HDFStore(hdf_path) as hdf:
            # this HDF contain pairwise DMG results
            for hypo in hypo_clusters:
                for hyper in hyper_clusters:
                    # if hypo hyper from different cell class, then use the major type to calculate
                    if cluster_level == 'SubType':
                        hypo_cell_class = self.sub_type_to_cell_class[hypo]
                        hyper_cell_class = self.sub_type_to_cell_class[hyper]
                        if hypo_cell_class != hyper_cell_class:
                            hypo = self.sub_type_to_major_type[hypo]
                            hyper = self.sub_type_to_major_type[hyper]

                    # weight on DMG for similar clusters (dist close to 1)
                    this_dist = self._cluster_dist[(hypo, hyper)]  # this is symmetric
                    records[(hypo, hyper)] = hdf[f'{hypo} vs {hyper}'] * this_dist  # AUROC * dist
                    records[(hyper, hypo)] = hdf[f'{hyper} vs {hypo}'] * -this_dist
        sorted_genes = pd.DataFrame(records).sum(axis=1).sort_values(ascending=False)
        final_genes = sorted_genes[sorted_genes > 0][:top_n]  # size <= top_n

        final_meta_table = self.gene_meta_table.loc[final_genes.index].reset_index(drop=True)
        final_meta_table['rank'] = (final_meta_table.index + 1).astype(int)

        # add gene size
        final_meta_table['gene_size'] = final_meta_table['end'] - final_meta_table['start']

        return final_meta_table

    def cluster_name_to_subtype(self, cluster_name):
        total_children = []
        if self.cluster_name_to_level[cluster_name] == 'SubType':
            total_children.append(cluster_name)
        else:
            for child in self.parent_to_children_list[cluster_name]:
                total_children += self.cluster_name_to_subtype(child)
        return total_children

    def annoj_url(self, active_clusters, chrom, start, end, track_type='CG', mc_track_height=50,
                  hide_sidebar=True, hide_toolbar=False, cell_type_color=True):
        # chrom, annoj removed chr...
        chrom = chrom.strip('chr')

        # active_clusters to track ids
        active_subtypes = []
        for cluster in active_clusters:
            active_subtypes += self.cluster_name_to_subtype(cluster)
        active_track_ids = [self._subtype_to_annoj_track_id[c] for c in active_subtypes]

        # track_type to mc_track_class
        if track_type.upper() == 'CG':
            mc_track_class = 'CG -CH -coverage'
        elif track_type.upper() == 'CH':
            mc_track_class = '-CG CH -coverage'
        elif track_type.lower():
            mc_track_class = '-CG -CH coverage'
        else:
            raise ValueError(f'Unknown track type: {track_type}')

        # color per track?
        if cell_type_color:
            track_palette = {self._subtype_to_annoj_track_id[k]: v[1:]  # remove # in hex
                             for k, v in self._palette['SubType'].items()
                             if k in active_subtypes}
        else:
            track_palette = None

        # location
        location = f'location={chrom}:{start}-{end}'

        # settings
        if hide_sidebar or hide_toolbar:
            accordion = 'accordion:"hide"' if hide_sidebar else ''
            toolbar = 'toolbar:"hide"' if hide_toolbar else ''
            _str = ','.join([accordion, toolbar])
            settings = 'settings={{{content}}}'.format(content=_str)
        else:
            settings = ''

        # config
        # All mC tracks
        all_track_str = '{{type:"MethTrack",height:{mc_track_height},class:"{mc_track_class}"}}'.format(
            mc_track_height=mc_track_height, mc_track_class=mc_track_class)
        total_items = [all_track_str]
        # specific track color
        if track_palette is not None:
            for track_id, color in track_palette.items():
                track_str = '{id:"' + track_id + '",color:{' + track_type + ':"' + color + '",rColor:1}}'
                total_items.append(track_str)
        config = f'config=[{",".join(total_items)}]'

        # active
        active = f"""active=[{",".join([f'"{t}"' for t in active_track_ids])}]"""

        total_url = f'{ANNOJ_URL_BASE}?{location}&{active}&{config}&{settings}'
        return total_url
