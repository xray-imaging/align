from setuptools import setup, find_packages, find_namespace_packages

setup(
    name='align',
    version=open('VERSION').read().strip(),
    #version=__version__,
    author='Viktor Nikitin, Francesco De Carlo',
    author_email='decarlof@gmail.com',
    url='https://github.com/xray-imaging/align.git',
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points = {
        'console_scripts': ['align=align.__main__:main'],
    },
    description='cli to run tomo auto alignment functions',
    zip_safe=False,
)
