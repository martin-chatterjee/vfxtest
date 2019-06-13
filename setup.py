from setuptools import setup, find_packages


with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='vfxtest',
    version='0.1.0',
    license='MIT',

    author='Martin Chatterjee',
    author_email='martin@chatterjee.de',

    description=('Manages a test suite across multiple python contexts'
                 ' commonly found in a VFX production environment'),
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/martin-chatterjee/vfxtest',
    project_urls={
        'Documentation' : 'https://vfxtest.readthedocs.org',
        'Source'        : 'https://github.com/martin-chatterjee/vfxtest',
        'Issues'        : 'https://github.com/martin-chatterjee/vfxtest/issues',
    },

    py_modules=[
        'vfxtest',
    ],
    scripts=[
        'bin/vfxtest.cmd',
        'bin/vfxtest',
    ],
    install_requires=[
        'virtualenv',
        'coverage >= 4.5',
        'mock >= 3.0; python_version < "3.3"',
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
    keywords=('unittest coverage tdd test driven development dcc vfx 3d '
              'animation pipeline nuke houdini hython maya mayapy nuke'),

    python_requires=('>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, '
                     '!=3.5.*, !=3.6.*, <4'),

)
