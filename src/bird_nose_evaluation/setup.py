from setuptools import find_packages, setup

package_name = 'bird_nose_evaluation'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Samarth Kabbur',
    maintainer_email='samarthKabbur@users.noreply.github.com',
    description='Bird Nose scenario files and run evaluation.',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'evaluate_run = bird_nose_evaluation.evaluate_run:main',
        ],
    },
)
