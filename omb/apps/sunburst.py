from plotly import graph_objects as go

from omb.backend import dataset


def create_sunburst(levels, selected_cells):
    if selected_cells is not None:
        data = dataset.get_variables(levels).loc[selected_cells]
    else:
        data = dataset.get_variables(levels)
    if 'SubType' in levels:
        data = data[data['SubType'].apply(lambda c: 'Outlier' not in c)]

    # prepare count table
    count_df = data.groupby(levels).apply(lambda i: i.shape[0]).reset_index()
    count_df.columns = levels + ['Cell Number']
    if 'RegionName' in count_df.columns:
        # some region name is the same as sub-region name, this cause error in sunburst js
        # add space in here and palette to distinguish
        count_df['RegionName'] = count_df['RegionName'].astype('str') + ' '

    # prepare total palette
    total_palette = {}
    for level in levels:
        palette = dataset.get_palette(level)
        if level == 'RegionName':
            palette = {k+' ': v for k, v in palette.items()}
        total_palette.update(palette)

    # prepare sunburst
    labels = []
    parents = []
    values = []
    colors = []
    for level, parent_level in zip(levels[::-1], levels[1::-1] + [None]):
        this_level_sum = count_df.groupby(level)['Cell Number'].sum().to_dict()
        this_level_sum = {k: v for k, v in this_level_sum.items() if v != 0}
        if parent_level is not None:
            this_parent_dict = count_df.set_index(level)[parent_level].to_dict()
        else:
            this_parent_dict = {label: '' for label in count_df[level].unique()}
        for label in this_level_sum.keys():
            labels.append(label)
            parents.append(this_parent_dict[label])
            values.append(this_level_sum[label])
            try:
                colors.append(total_palette[label])
            except KeyError:
                colors.append('#D3D3D3')

    # Here is a sunburst example
    # fig = go.Figure(go.Sunburst(
    #     labels=["Eve", "Cain", "Seth", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
    #     parents=["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve"],
    #     values=[65, 14, 12, 10, 2, 6, 6, 4, 4],
    #     branchvalues="total",
    # ))
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker={'colors': colors},  # only in this way, I can precisely control the color
        branchvalues="total",
    ))
    # Update layout for tight margin
    # See https://plotly.com/python/creating-and-updating-figures/
    fig.update_layout(margin=dict(t=15, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig
