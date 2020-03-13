"""
Dataset contain everything related to the apps, provides api that's used by apps
"""
import pathlib


def validate_dataset_dir(path: pathlib.Path):
    try:
        assert path.exists()
    except AssertionError:
        print(f'Dataset directory {path} do not exist')


class Dataset:
    def __init__(self, dataset_dir):
        self.dataset_dir = pathlib.Path(dataset_dir)

    pass
