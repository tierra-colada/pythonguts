import setuptools

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name='pythonguts',
    version='0.1.0',
    packages=setuptools.find_packages(),
    url='https://github.com/tierra-colada/pythonguts',
    license='MIT',
    author='kerim khemrev',
    author_email='tierracolada@gmail.com',
    description='Tool aimed at python code correction that allows to '
                'automatically find and replace function definition',
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url='https://github.com/tierra-colada/pythonguts/archive/refs/tags/v0.1.0.tar.gz',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='py-parser python-parser py-editor python-editor py-generator python-generator',
    entry_points={
        'console_scripts': ['editpy=pythonguts.editpy:main']
    },
    python_requires='>=3',
    install_requires=[
        'wheel',
        'astor',
    ],
    include_package_data=True   # important to copy MANIFEST.in files
)
