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
for n in subjectslist:
    file = n + '.pkl'
    fileopen = open(file, 'rb')
    subjects[n] = pickle.load(fileopen)
    fileopen.close()
    trialnames = list(set(subjects[n].keys()))

# CHOOSE WHAT TO PLOT
print("The trials to choose from are: " + ", ".join(trialnames))
print('Please enter trials to use, separated by commas')
trials = input().split(',')
for trial in trials:
    if trial not in trialnames:
        raise Exception('Trial %s does not exist' % (trial, ))

paramnames = [x for x in subjects[subjectslist[0]][trials[0]] if type(subjects[subjectslist[0]][trials[0]][x]) is float]
print("The parameters you can plot are: " + ", ".join(paramnames))
print('Please enter parameter to use')
paramname = input()

# PLOT THE THING
data = [[]]*len(trials)
for subjectnum in range(len(subjectslist)):
    subject = subjectslist[subjectnum]
    for trialnum in range(len(trials)):
        trial = trials[trialnum]
        data[trialnum].append(subjects[subject][trial][paramname])

#Box & whisker plot http://matplotlib.org/examples/statistics/boxplot_demo.html
plt.boxplot(data, labels=trialnames)
import pdb; pdb.set_trace()