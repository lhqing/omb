def n_cell_to_marker_size(n_cells):
    if n_cells >= 100000:
        size = 1.5
    elif n_cells >= 50000:
        size = 2
    elif n_cells >= 20000:
        size = 2.5
    elif n_cells >= 10000:
        size = 3
    elif n_cells >= 5000:
        size = 3.5
    elif n_cells >= 1000:
        size = 4
    elif n_cells >= 500:
        size = 5
    elif n_cells >= 100:
        size = 6
    elif n_cells >= 50:
        size = 7
    elif n_cells >= 10:
        size = 8
    else:
        size = 9
    return size
