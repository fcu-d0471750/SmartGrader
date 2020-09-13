import os
import pandas as pd

command = ["jupyter nbextension install --user --py nbgrader --overwrite",
           "jupyter nbextension enable --user --py nbgrader",
           "jupyter serverextension enable --user --py nbgrader",
           "jupyter nbextension disable --user create_assignment/main",
           "jupyter nbextension disable --user formgrader/main --section=tree",
           "jupyter serverextension disable --user nbgrader.server_extensions.formgrader",]

for cmd in command:
    os.system(cmd)
