from glob import glob

from setuptools import find_packages, setup

package_name = 'bird_nose_algorithms'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Samarth Kabbur',
    maintainer_email='samarthKabbur@users.noreply.github.com',
    description='Bird Nose autonomy nodes.',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'status_node = bird_nose_algorithms.status_node:main',
        ],
    },
)
