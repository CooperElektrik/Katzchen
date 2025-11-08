from setuptools import setup, find_packages

setup(
    name='katzchen',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={},
    author='CooperElektrik',
    description='A Markdown-flavored domain-specific language for the Katzen Visual Novel Engine.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/CooperElektrik/katzchen', # Replace with your project's URL
    python_requires='>=3.9',
    license="MIT"
)
