from plotly import graph_objects as go

from omb.backend import dataset


def create_sunburst(levels, selected_cells):
    if selected_cells is not None:
        data = dataset.get_variables(levels).loc[selected_cells]
    else:
        data = dataset.get_variables(levels)
    if 'SubType' in levels:
        data = data[data['SubType'].apply(lambda c: 'Outlier' not in c)]
    total_cell = data.shape[0]

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
            palette = {k + ' ': v for k, v in palette.items()}
        total_palette.update(palette)

    # prepare sunburst
    labels = []
    parents = []
    values = []
    colors = []
    proportion_total = []
    proportion_parent = []
    for level, parent_level in zip(levels[::-1], levels[1::-1] + [None]):
        this_level_sum = count_df.groupby(level)['Cell Number'].sum().to_dict()
        this_level_sum = {k: v for k, v in this_level_sum.items() if v != 0}
        if parent_level is not None:
            this_parent_dict = count_df.set_index(level)[parent_level].to_dict()
            parent_level_sum = count_df.groupby(parent_level)['Cell Number'].sum().to_dict()
            parent_level_sum = {k: v for k, v in parent_level_sum.items() if v != 0}
        else:
            this_parent_dict = {label: '' for label in count_df[level].unique()}
            parent_level_sum = {}
        for label in this_level_sum.keys():
            labels.append(label)
            parent = this_parent_dict[label]
            parents.append(parent)
            values.append(this_level_sum[label])
            proportion_total.append(f'{this_level_sum[label] / total_cell * 100: .2f}% of total')
            if parent != '':
                proportion_parent.append(
                    f'{this_level_sum[label] / parent_level_sum.get(parent, total_cell) * 100: .2f}%'
                    f' of {this_parent_dict[label]}')
            else:
                proportion_parent.append('')
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
        customdata=[*zip(proportion_total, proportion_parent)],
        marker={'colors': colors},  # only in this way, I can precisely control the color
        branchvalues="total",
        hoverlabel=None,
        hovertemplate='<b>%{label} </b> '
                      '<br>- %{value} nuclei'
                      '<br>-%{customdata[1]}'
                      '<br>-%{customdata[0]}<extra></extra>'
    ))
    # Update layout for tight margin
    # See https://plotly.com/python/creating-and-updating-figures/
    fig.update_layout(margin=dict(t=15, l=0, r=0, b=15),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig
