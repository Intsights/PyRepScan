import setuptools
import os
import glob


setuptools.setup(
    name='PyRepScan',
    version='0.2.2',
    author='Gal Ben David',
    author_email='gal@intsights.com',
    url='https://github.com/intsights/PyRepScan',
    project_urls={
        'Source': 'https://github.com/intsights/PyRepScan',
    },
    license='MIT',
    description='A Git Repository Leaks Scanner Python library written in C++',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='git repository leaks scanner detector libgit2 re2 c++',
    python_requires='>=3.6',
    zip_safe=False,
    tests_require=[
        'gitpython',
    ],
    package_data={},
    include_package_data=True,
    ext_modules=[
        setuptools.Extension(
            name='pyrepscan',
            sources=glob.glob(
                pathname=os.path.join(
                    'src',
                    'git_repository_scanner.cpp',
                ),
            ),
            language='c++',
            extra_compile_args=[
                '-Ofast',
                '-std=c++17',
            ],
            extra_link_args=[
                '-lre2',
                '-lgit2',
                '-lpthread',
            ],
            include_dirs=[
                'src',
            ],
        ),
    ],
)
