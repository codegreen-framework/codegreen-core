from setuptools import setup, find_packages

setup(
    name='codegreen_core',
    version='0.1',
    include_package_data=True,
    package_data={
        'codegreen_core.data': ['country_list.json','ci_default_values.csv'],
    },
    packages=find_packages(),
    install_requires=["pandas","numpy","entsoe-py","redis"]
)
