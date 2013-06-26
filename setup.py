from setuptools import setup

setup(
    name='cbmock',
    version='0.3.2',
    description='Couchbase mock server',
    author='Pavel Paulau',
    author_email='pavel.paulau@gmail.com',
    packages=['cbmock'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['cbmock = cbmock.cbmock:main']
    },
    install_requires=[
        'requests==1.2.0',
        'twisted',
        'cbtestlib'
    ],
    setup_requires=[],
    tests_require=['lettuce', 'nose', 'requests'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
