from setuptools import setup, find_packages

setup(
    name='ambient_bd_downloader',
    version='0.4.0',
    description='Download data from Somnofy devices',
    long_description_content_type="text/markdown",
    url='https://github.com/chronopsychiatry/Ambient-BD-VitalThings-API-Data-Access',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'pandas>=1.5.3',
        'requests>=2.31.0'
    ],
    entry_points={
        'console_scripts': [
            'ambient_download=ambient_bd_downloader:main.main',
            'ambient_generate_config=ambient_bd_downloader:generate_config.generate_config'
        ],
    },
)
