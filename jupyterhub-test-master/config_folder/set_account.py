import os
from subprocess import call
import pandas as pd

df = pd.read_csv("account.csv", encoding='utf-8')

nids = df.username.to_list()

pwd='chishong656123'

for nid in nids:
        call('echo {} | sudo -S {}'.format(pwd, "docker exec --user " + nid + " jupyterhub python set_nbgrader.py"), shell=True)
