from os.path import dirname, isfile, join, realpath, sep

from setuptools import setup

from version import version_info

base_url = 'https://github.com/thevickypedia/Jarvis'

# https://pypi.org/classifiers/
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Information Technology',
    'Operating System :: MacOS :: MacOS X',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.9',
    'Topic :: Multimedia :: Sound/Audio :: Speech',
    'Topic :: Scientific/Engineering :: Human Machine Interfaces',
    'Topic :: Scientific/Engineering :: Image Recognition',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
    'Topic :: Multimedia :: Sound/Audio :: Conversion',
    'Natural Language :: English'
]


def read(name: str) -> str:
    """Reads the file that was received as argument.

    Args:
        name: Name of the file that has to be opened and read.

    Returns:
        str:
        Content of the file that was read.

    References:
        https://pythonhosted.org/an_example_pypi_project/setuptools.html#setting-up-setup-py
    """
    with open(join(dirname(__file__), name)) as file:
        content = file.read()
    return content


def dependencies() -> list:
    """Gathers dependencies from requirements file.

    Returns:
        list:
        List of dependencies to be installed.
    """
    requirement_file = dirname(realpath(__file__)) + f'{sep}lib{sep}requirements.txt'
    if isfile(requirement_file):
        with open(requirement_file) as requirements:
            install_requires = requirements.read().splitlines()
    return install_requires


setup(
    name='jarvis-ironman',
    version='.'.join(str(c) for c in version_info),
    description="IronMan's Jarvis with python.",
    long_description=read('README.md') + '\n\n' + read('CHANGELOG'),
    long_description_content_type='text/markdown',
    author='Vignesh Sivanandha Rao',
    author_email='svignesh1793@gmail.com',
    License='MIT',
    url=base_url,
    python_requires=">=3.8",
    install_requires=dependencies(),
    classifiers=classifiers,
    keywords='python, natural-language-processing, text-to-speech, speech-recognition, jarvis, hotword-detection,'
             'virtual-assistant, multiprocessing, threadpool',
    download_url=f'{base_url}/archive/master.zip',
    project_urls={
        'Source': base_url,
        'Docs': 'https://thevickypedia.github.io/Jarvis',
        'Demo': 'https://vigneshrao.com/Jarvis/Jarvis_Demo.mp4',
        'Bug Tracker': f'{base_url}/issues'
    },
    zip_safe=True
)
