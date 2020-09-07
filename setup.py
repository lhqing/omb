from setuptools import setup, find_packages

omb_version = '0.1'

setup(
    name='omb',
    version=omb_version,
    author='Hanqing Liu',
    author_email='hanliu@salk.edu',
    packages=find_packages(),
    description='Online mouse brain.',
    long_description=open('README.md').read(),
    include_package_data=True,
    package_data={
        '': ['*.msg', '*.ply', '*.h5', '*.csv', '*.json', '*.lib', '*.css', '*.js', '*.png', '*.jpeg']
    },
    install_requires=[
        'dash',
        'numpy',
        'pandas',
        'tables',  # required by pandas to read hdf5
        'xarray',
        'msgpack',
        'plotly',
        'joblib',
        'plyfile'
    ],
)

if __name__ == '__main__':
    pass
