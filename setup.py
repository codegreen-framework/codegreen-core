from setuptools import setup, find_packages

setup(
    name='codegreen_core',
    version='0.5.0',
    include_package_data=True,
    package_data={
        'codegreen_core.utilities': ['country_list.json','ci_default_values.csv','model_details.json'],
    },
    packages=find_packages(),
    install_requires=["pandas","numpy","entsoe-py","redis","tensorflow","scikit-learn","sphinx"]
)
