from distutils.core import setup

MATPLOTLIB_MIN_VERSION = '3.9.2'
NUMPY_MIN_VERSION = '1.26.4'
PANDAS_MIN_VERSION = '2.2.2'
PLOTLY_MIN_VERSION = '5.24.1'
PULP_MIN_VERSION = '2.9.0'
PYTEST_MIN_VERSION = '8.3.3'
SCIKITLEARN_MIN_VERSION = '1.5.2'
STREAMLIT_MIN_VERSION = '1.38.0'
TSG_CLIENT_GIT = 'tsg-client @ git+https://github.com/CPES-Power-and-Energy-Systems/tsg-client.git'

setup(
    name='ewh-flex',
    version='0.4.0',
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
        'matplotlib >= {0}'.format(MATPLOTLIB_MIN_VERSION),
        'numpy >= {0}'.format(NUMPY_MIN_VERSION),
        'pandas >= {0}'.format(PANDAS_MIN_VERSION),
        'plotly >= {0}'.format(PLOTLY_MIN_VERSION),
        'PuLP >= {0}'.format(PULP_MIN_VERSION),
        'pytest >= {0}'.format(PYTEST_MIN_VERSION),
        'scikit-learn >= {0}'.format(SCIKITLEARN_MIN_VERSION),
        'streamlit >= {0}'.format(STREAMLIT_MIN_VERSION),
        TSG_CLIENT_GIT
    ],
)
