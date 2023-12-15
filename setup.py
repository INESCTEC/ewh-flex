from distutils.core import setup

PANDAS_MIN_VERSION = '2.1.4'
NUMPY_MIN_VERSION = '1.26.2'
SKLEARN_MIN_VERSION = '1.3.2'


setup(
    name='ewh-flex',
    version='0.1.0',
    packages=['ewh_flex'],
    url='',
    license_files=('LICENSE',),
    author='José Paulos',
    author_email='jose.paulos@inesctec.pt',
    description='EWH Flex: This tool focuses on optimizing the functioning '
                'calendar of thermoelectric water heaters (EWH) through the '
                'analysis of the EWH consumption diagram. Ensures the delivery '
                'of consumer-defined comfort levels, subject to certain '
                'constraints, while simultaneously minimizing operational '
                'costs or total energy consumption.',
    install_requires=[
        'pandas >= {0}'.format(PANDAS_MIN_VERSION),
        'numpy >= {0}'.format(NUMPY_MIN_VERSION),
        'scikit-learn >= {0}'.format(SKLEARN_MIN_VERSION)
    ],
)
