import os


# This points to the root of the project repository.
# It is useful for loading resources.
#
# WARNING: This depends on the location the program is run from.
# If you run a test while in a subdirectory of the project, it will
# be incorrect.
PROJECT_DIRECTORY = os.path.join(os.pardir, os.getcwd()) + "/"
