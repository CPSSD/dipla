# dipla

## Setting Up your Development Environment

### Pre-requisites

* To set up the project, you will need...
    * git
    * python 3.4
    * pip
    * virtualenv

### Instructions

1. Clone the repository: `git clone https://www.github.com/cpssd/dipla.git`

2. Change directory to project root: `cd dipla`

3. Create your virtual environment: `virtualenv venv --python=<python3_path>`
    * Linux: `virtualenv venv --python=/usr/bin/python3`

4. Activate your virtual environment: `source venv/bin/activate`

5. Install the project dependencies: `pip install --upgrade -r requirements.txt`

You can now write code for the project!

### Notes

* If you install additional dependencies with pip, you can update the requirements file using `pip freeze > requirements.txt`

* Remember to deactivate the virtual environment when you're done using `deactivate`

## Running the tests

You can run all the tests with: `nosetests`

## Checking Code Style

You can check if your code complies with the PEP8 style guide using `pep8`.

* Checking all of the tests: `pep8 tests`

* Checking all of the production code: `pep8 dipla`

