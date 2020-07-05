from dash.exceptions import PreventUpdate

from omb.backend import dataset


def get_split_plot_df(coord_base, variable_name, selected_cells, hover_cols=('RegionName', 'SubType')):
    hue_palette = dataset.get_palette(variable_name)
    plot_df = dataset.get_coords(coord_base)

    cell_region_names = dataset.get_variables('RegionName')

    # some coords do not have all cell so selected index need to be updated
    selected_cell_index = selected_cells & plot_df.index
    if len(selected_cell_index) == 0:
        raise PreventUpdate
    unselected_cell_index = plot_df.index[~plot_df.index.isin(selected_cell_index)]

    hover_cols = list(hover_cols)
    # add hover data and color data
    if variable_name not in hover_cols:
        hover_cols.append(variable_name)
    for col_name in hover_cols:
        plot_df[col_name] = dataset.get_variables(col_name).astype(str)

    # selected
    selected_plot_df = plot_df.loc[selected_cell_index]
    unselected_plot_df = plot_df.loc[unselected_cell_index]
    return selected_plot_df, unselected_plot_df, hover_cols, hue_palette


def n_cell_to_marker_size(n_cells):
    if n_cells > 20000:
        size = 1
    elif n_cells > 10000:
        size = 2
    elif n_cells > 5000:
        size = 3
    elif n_cells > 1000:
        size = 4
    elif n_cells > 500:
        size = 5
    elif n_cells > 100:
        size = 6
    elif n_cells > 50:
        size = 7
    elif n_cells > 10:
        size = 8
    else:
        size = 9
    return size

