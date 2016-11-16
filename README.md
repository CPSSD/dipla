# dipla

## Setting Up your Development Environment

### Pre-requisites

* To set up the project, you will need...
    * git
    * python 3.5
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

### Documentation

To generate documentation we use [pydoc](https://docs.python.org/3.2/library/pydoc.html).

It can be run with `python3 -m pydoc dipla/server/task_queue.py` where `task_queue.py` can be replaced by the file you want documentation on.

### Notes

* If you install additional dependencies with pip, you can update the requirements file using `pip freeze > requirements.txt`

* Remember to deactivate the virtual environment when you're done using `deactivate`

## Running the tests

You can run all the tests with: `nosetests`

## Checking Code Style

You can check if your code complies with the PEP8 style guide using `pep8`.

* Checking all of the tests: `pep8 tests`

* Checking all of the production code: `pep8 dipla`

### Code Example

Here's an example of some code you could write and distribute.

```python
import functools
from dipla.api.decorators import distributable
from dipla.api.decorators import task_input

@distributable
def square(number):
    return number**2

@distributable
def remove_large(result, output_values):
    if result > 1000000:
        return
    else:
        output_values.append(result)


@task_input
def fetch_number_from(database):
    next_number = int(database.get_next())
    return next_number


def driver():
    database = get_database()
    input_instructions = functools.partial(fetch_number_from, database)
    result = square(input_instructions)
    filtered = []
    filter(result, filtered)
    dipla.api.run()
```
