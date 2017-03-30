from os import path
from collections import defaultdict
from pprint import pprint
import sys

# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))
from dipla.api import Dipla


@Dipla.distributable()
def get_job_industry(j_id):
    import requests
    u = 'http://job-openings.monster.ie/v2/job/View?JobID={}'.format(j_id)
    txt = requests.get(u).text
    job_box = '<div id="JobSummary" class="panel-body m-job-summary">'
    industry_box = 'itemprop="industry">'

    jb_i = txt.find(job_box)
    if jb_i == -1:
        return None
    indust_start = txt[jb_i:].find(industry_box)
    if indust_start == -1:
        return None
    indust_start += len(industry_box) + jb_i
    indust_end = txt[indust_start:].find('<') + indust_start
    return txt[indust_start:indust_end]


indust_list = Dipla.apply_distributable(
    get_job_industry,
    list(range(182412598 - 20, 182412598)))


invalid = 0
industries = defaultdict(int)
for indst in Dipla.get(indust_list):
    if indst:
        industries[indst] += 1
    else:
        invalid += 1

print(invalid)
pprint(industries)
