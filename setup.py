from setuptools import setup, find_packages
import sys, os

version = '0dev'
shortdesc = 'Access ldap via a dictionary tree.'
#longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='dicttree.ldap',
      version=version,
      description=shortdesc,
      #long_description=longdesc,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        ],
      keywords='',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='http://github.com/chaoflow/dicttree.ldap',
      license='BSD license',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['dicttree'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
        'setuptools',
        ],
      )
