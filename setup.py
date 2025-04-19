from setuptools import setup, find_packages

setup(
    name="deepseek_chat",
    version="0.1.1",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=['requests', 'urllib3<2.0'],
    author="coodar",
    author_email="coodar@gmail.com",
    description="A Python package for interacting with DeepSeek API",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/coodar/deepseek_client",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'dscli=cli.deepseek_client:main',
        ],
    },
    package_data={
        '': ['README.md', '**/*.py'],
    },
)