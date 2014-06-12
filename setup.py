import sys
try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup

setup(
    name='groot',
    version='0.0.1',
    author='Gary Johnson',
    author_email = 'gary@gjtt.com',
    description = 'Automation for BDD testing PyQt apps',
    install_requires=['bottle', 'PyQt5'],
    tests_require=['bottle', 'PyQt5'],
    license = 'MIT License',
    py_modules = ['groot'],
    )
