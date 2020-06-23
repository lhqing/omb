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
        '': ['*.msg', '*.h5', '*.csv']
    },
    install_requires=[
        'dash==1.9.1',
        'numpy==1.18.1',
        'pandas==1.0.2',
        'tables==3.6.1',  # required by pandas to read hdf5
        'xarray==0.15.0',
        'msgpack==1.0.0', 'plotly'
    ],
)

if __name__ == '__main__':
    pass
