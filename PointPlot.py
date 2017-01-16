# -*- coding: utf-8 -*-
"""
Data plotting: comparison between trials - multiple subjects

@author: Simon Marchant 2017
"""

import pickle
from matplotlib import pyplot as plt

# INITIAL SETUP
print("""Please provide the pickle file(s) to read from,
separating files with commas (e.g. 'Subject1,Subject2')
Note: if a file is in a subfolder, add path (e.g. 'Angles/Subject1')""")
subjectslist = input().split(',')
subjects = {}
trialnamesets = []
for n in subjectslist:
    file = n + '.pkl'
    fileopen = open(file, 'rb')
    subjects[n] = pickle.load(fileopen)
    fileopen.close()
    trialnamesets.append(set(subjects[n].keys()))
trialnames = list(set.intersection(*trialnamesets))

# CHOOSE WHAT TO PLOT
print("The trials to choose from are: " + ", ".join(trialnames))
trials = input('Please enter trials to use, separated by commas').split(',')
for trial in trials:
    if trial not in trialnames:
        raise Exception('Trial %s does not exist' % (trial, ))

paramnames = [x for x in subjects[subjectslist[0]][trials[0]] if type(subjects[subjectslist[0]][trials[0]][x]) is float]
print("The parameters you can plot are: " + ", ".join(paramnames))
paramname = input('Please enter parameter to use, separated by commas')

# PLOT THE THING
data = range(trialnames)
for subjectnum in range(subjectslist):
    subject = subjectslist[subjectnum]
    for trialnum in range(trialnames):
        trial = trialnames[trialnum]
        data[trial].append(subjects[subject][trial])

#Box & whisker plot http://matplotlib.org/examples/statistics/boxplot_demo.html
plt.boxplot(data, labels=trialnames)