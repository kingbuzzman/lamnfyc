from setuptools import setup, find_packages

setup(
    name='lamnfyc',
    version='0.0.1',
    description="Virtual Environment builder",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
    ],
    keywords='setuptools deployment installation distutils',
    author='Javier Buzzi',
    author_email='buzzi.javier@gmail.com',
    license='MIT',
    packages=find_packages('.'),
    install_requires=[
        'pyliblzma==0.5.3',
        'futures==3.0.5',
        'pyyaml==3.12',
        'jinja2==2.8',
    ],
    entry_points={
        'console_scripts': ['lamnfyc=lamnfyc.cli:main'],
    })
