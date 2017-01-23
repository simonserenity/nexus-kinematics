# -*- coding: utf-8 -*-
"""
Kinematics analysis: multiple trials - single subject

Simon Marchant 2017
"""

import csv
import numpy as np
import pickle

def csvread(file):
    """
    Read a CSV file and output a numpy array object of that file.
    """
    thisfile = open(file)
    thisreader = csv.reader(thisfile)
    filelist = np.array(list(thisreader))
    return filelist
    
#def tableread(filelist, start, frames):
    
    
def readtrajectories(filelist, frames):
    """
    Read a numpy array object in Vicon export format with marker trajectories.
    Requires frame dictionary with initial contact, foot off, and end of swing.
    Values that cannot be calculated from inputs will output 'NA'.
    Output is a dictionary with the following parts:-
    LeftToeZ/RightToeZ = vector of toe marker Z coord throughout trial
    LeftStepTime/RightStepTime = time taken for marked step, in seconds
    LeftFoffFraction/RightFoffFraction = footoff as fraction of total step time
    LeftStepLen/RightStepLen = length of marked step length in metres
    LeftSpeedCalc/RightSpeedCalc = walking speed calculated from these values
    """
    filelen = len(filelist) - 2
    trajstart = filelen
    output = {}
    LtoeZ = []
    RtoeZ = []
    LeftToeCol = 29
    RightToeCol = 47
    for row in range(filelen):
        try:
            # Assign gait parameters to dictionary
            if filelist[row][0] == 'Trajectories':
                trajstart = row + 5
                filewidth = len(filelist[row+3])-1
        except IndexError:
            continue
    for col in range(2,filewidth):
        # Name the trajectory in each column
        if filelist[trajstart-3][col]:
            tmp = filelist[trajstart-3][col]+filelist[trajstart-2][col]
        elif filelist[trajstart-3][col-1]:
            tmp = filelist[trajstart-3][col-1]+filelist[trajstart-2][col]
        elif filelist[trajstart-3][col-2]:
            tmp = filelist[trajstart-3][col-2]+filelist[trajstart-2][col]
        name = tmp[tmp.rfind(":")+1:]
        output[name] = []
        side = ('Right') if name[0]=='R' else ('Left')
        # Make a list of values within the marked stride frames
        for row in range(trajstart+frames[side+'Start'], trajstart+frames[side+'End']):
            if filelist[row][col] == '':
                output[name].append('NA')
            else:
                output[name].append(float(filelist[row][col]))
    sides = ['Left', 'Right']
    for side in sides:
#        try:
            # Start & end frames are min& max because Nexus confuses them sometimes.
            # And if it does that, it doesnt show step time/speeds
            output[side+'StepTime'] = (frames[side+'End']-frames[side+'Start'])/100
            output[side+'FoffFraction'] = (frames[side+'Foff']-frames[side+'Start']) / output[side+'StepTime']
            try:
                output[side+'StepLen'] = float(filelist[frames[side+'End']+trajstart][locals()[side+'ToeCol']+1]) - float(filelist[frames[side+'Start']+trajstart][locals()[side+'ToeCol']+1])
            except ValueError:
                output[side+'StepLen'] = 'NA'
            output[side+'SpeedCalc'] = output[side+'StepLen'] / output[side+'StepTime']
#        except TypeError:
#            print('TypeError caught, suspect missing trajectory values in stride. Continuing...')
    #import pdb; pdb.set_trace()
    return output
    
def readangles(filelist):
    """
    Read a numpy array object in Vicon export format with model outputs.
    Output is a dictionary with the following parts:-
    LeftStartFrame/RightStartFrame = frame of initial footstrikes in marked stride
    LeftEndFrame/RightEndFrame = frame of final footstrikes in marked stride
    LeftAnkleAngle/RightAnkleAngle = list of absolute ankle angles throughout trial
    LeftSpeed/RightSpeed = walking speed
    LeftFoffFrame/RightFoffFrame = frame of foot off in marked stride
    StrideLen = stride length in marked stride
    """
    filelen = len(filelist) - 2
    output = {'RightAnkleAngle': [], 'LeftAnkleAngle': [], 'Frames': {}}
    anglestart = filelen
    LeftStrike = []
    RightStrike = []
    events = 0
    for n in range(filelen):
        try:
            if filelist[n][0] == 'Model Outputs':
                anglestart = n + 5
                filewidth = len(filelist[n+3])-1
            elif filelist[n][0] == 'Events':
                events = 1
            elif filelist[n][2] == 'Walking Speed':
                output[filelist[n][1]+'Speed'] = float(filelist[n][3])
            elif filelist[n][2] == 'Foot Off' and events == 1:
                # Footoff frame in events
                output['Frames'].update({filelist[n][1]+'Foff' : int(float(filelist[n][3]) * 100)})
            elif filelist[n][2] == 'Stride Length':
                output[filelist[n][1]+'StrideLen'] = float(filelist[n][3])
            elif filelist[n][2] == 'Foot Strike': 
                # Convert seconds to frames at 100Hz.
                if filelist[n][1] == 'Left':
                    LeftStrike.append(int(float(filelist[n][3]) * 100))
                elif filelist[n][1] == 'Right':
                    RightStrike.append(int(float(filelist[n][3]) * 100)) 
            elif n >= anglestart:
                # List ankle abs angles, convert to float if possible
                try:
                    output['LeftAnkleAngle'].append(float(filelist[n][2]))
                except ValueError:
                    output['LeftAnkleAngle'].append(filelist[n][2])
                try:
                    output['RightAnkleAngle'].append(float(filelist[n][101]))
                except ValueError:
                    output['RightAnkleAngle'].append(filelist[n][101])
        except IndexError:
            continue
    sides = ['Left', 'Right']
    for side in sides:
        output['Frames'].update({side+'Start' : min(locals()[side+'Strike'])})
        output['Frames'].update({side+'End' : max(locals()[side+'Strike'])})
    #import pdb; pdb.set_trace()
    if anglestart == filelen:
        raise NameError('No angles in angle file!')
    return output

def onetrial(trialnum):
    """
    Read in files for a single trial, extract useful information. 
    Data must be in CSV files in subdirectories Angles and Trajectories.
    Gives an empty dictionary if no stride data present in angles file.
    """
    eventsexist = False
    anglelist = csvread("Angles/%s.csv" % (trialnum, ))
    for n in range(len(anglelist)):
        for m in range(len(anglelist[n])):
            if anglelist[n][m] == 'Events':
                eventsexist = True
    if eventsexist == False:
        print("WARNING: no events in angles file, aborting with empty output.")
        return {}
    angles = readangles(anglelist)
    trajlist = csvread("Trajectories/%s.csv" % (trialnum, ))
    trajectories = readtrajectories(trajlist, angles['Frames'])
    output = {**trajectories, **angles}
    #import pdb; pdb.set_trace()
    return output

def minclearance(ToeZ, StartFrame, FootOff, EndFrame, MidSwingStart, MidSwingEnd):
    """
    Returns the minimum foot clearance in middle of swing in marked stride.
    Inputs: Toe marker Z (list), Start frame, foot off frame, end frame, start fraction of mid swing, end fraction of mid swing.
    Output: minimum clearance, frame it occurs at.
    """
    swing = ToeZ[FootOff:EndFrame]
    ground = min(ToeZ[StartFrame:EndFrame])
    middleframes = [(FootOff+int(MidSwingStart*len(swing))),(EndFrame-int(MidSwingEnd*len(swing)))]
    MinZ = min(ToeZ[middleframes[0]:middleframes[1]])
    clearance = MinZ - ground
    return clearance

def arraycleaner(array):
    """
    Make numpy array rows the same length by shortening long ones.
    """
    lengths = [len(x) for x in array]
    #shortindex = lengths.index(min(lengths))
    shortest = min(lengths)
    for n in range(len(array)):
        line = array[n]
        if len(array[n]) != shortest:
            this = len(line)
            cut = np.ceil(1/((this/shortest) - 1))
            #import pdb; pdb.set_trace()
            for m in range(len(array[n])):
                if m % cut == 0 and m != 0:
                    line[m] = 'del'
            for m in range(len(array[n])):
                try:
                    if line[m] == 'del':
                        del line[m]
                except IndexError:
                    continue
            array[n] = line[0:shortest]
    return array
    
if __name__ == '__main__':
    trials = ['OWN','FACTORY','R0','R50','R100','R150','R300','X0','X50','X100','X150','X300','D50','D100','D150']
    #TEST CASE (comment out the above line, uncomment line below this)
    #trials = ['OWN']
    subject = {}
    print("Please enter the participant ID, e.g. 1")
    participant = input()
    print("Please enter the affected side, e.g. Left. If both, enter Bilateral.")
    affectedside = input().capitalize()
    if affectedside not in ('Left', 'Right', 'Bilateral'):
        raise ValueError("GOD DAMNIT ENTER LEFT OR RIGHT OR BILATERAL. WHAT THE HELL.")
    for trial in trials:
        print("""Please enter the trial number for %s. If none, leave blank.""" % (trial, ))
        trialnum = input()
        if trialnum == '':
            subject[trial] = {}
        else:
            subject[trial] = onetrial(trialnum)
            subject[trial]['AffectedSide'] = affectedside
    afile = open(r'Subject%s.pkl' % (participant, ), 'wb')
    pickle.dump(subject, afile)
    afile.close()
