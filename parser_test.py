# parser_test.py

from parser import *

data = get_data()

soul = data[0]

jobs = soul.getAllDescendantsOfType(LineType.JOB)

job = jobs[0]

abs = abilities = job.getAllDescendantsOfType(LineType.ABILITY)
kw = keyword = job.getDescendantOfType(LineType.KEYWORD)
t = trait = job.getDescendantOfType(LineType.TRAIT)
lb = job.getDescendantOfType(LineType.LB)