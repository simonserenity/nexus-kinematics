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
    
def readtrajectories(filelist, LeftStartFrame, LeftEndFrame, LeftFoffFrame, RightStartFrame, RightEndFrame, RightFoffFrame):
    """
    Read a numpy array object in Vicon export format with marker trajectories.
    Requires frame of initial contact, foot off, and end of swing.
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
    for n in range(filelen):
        try:
            # Assign gait parameters to dictionary
            if filelist[n][0] == 'Trajectories':
                trajstart = n + 5
                for m in range(len(filelist[trajstart-3])):
                    if 'LTOE' in filelist[n][m]:
                        LeftToeCol = m
                    elif 'RTOE' in filelist[n][m]:
                        RightToeCol = m                   
            elif n >= trajstart:
                LtoeZ.append(filelist[n][LeftToeCol + 2])
                RtoeZ.append(filelist[n][RightToeCol + 2])
        except IndexError:
            continue
    output['LeftToeZ'] = [(0 if n=='' else float(n)) for n in LtoeZ]
    output['RightToeZ'] = [(0 if n=='' else float(n)) for n in RtoeZ]
    sides = ['Left', 'Right']
    #TODO: change all endframe/startframe/foffframe to use function inputs
    for side in sides:
#        try:
            # Start & end frames are min& max because Nexus confuses them sometimes.
            # And if it does that, it doesnt show step time/speeds
            output[side+'StepTime'] = (output[side+'EndFrame']-output[side+'StartFrame'])/100
            output[side+'FoffFraction'] = (output[side+'FoffFrame']-output[side+'StartFrame']) / output[side+'StepTime']
            output[side+'StepLen'] = float(filelist[output[side+'EndFrame']][locals()[side+'ToeCol']+1]) - float(filelist[output[side+'StartFrame']][locals()[side+'ToeCol']+1])
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
    output = {'RightAnkleAngle': [], 'LeftAnkleAngle': []}
    anglestart = filelen
    LeftStrike = []
    RightStrike = []
    events = 0
    for n in range(filelen):
        try:
            if filelist[n][0] == 'Model Outputs':
                anglestart = n + 5
            elif filelist[n][0] == 'Events':
                events = 1
            elif filelist[n][2] == 'Walking Speed':
                output[filelist[n][1]+'Speed'] = float(filelist[n][3])
            elif filelist[n][2] == 'Foot Off' and events == 1:
                # Footoff frame in events
                output[filelist[n][1]+'FoffFrame'] = int(float(filelist[n][3]) * 100)
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
    #import pdb; pdb.set_trace()
    sides = ['Left', 'Right']
    for side in sides:
        output[side+'StartFrame'] = min(locals()[side+'Strike'])
        output[side+'EndFrame'] = max(locals()[side+'Strike'])
    return output

def onetrial(trialnum):
    """
    Read in files for a single trial, extract useful information.
    """
    #TODO: check trials for an Events section, output something obviously blank if not there.
    anglelist = csvread("Angles/%s.csv" % (trialnum, ))
    angles = readangles(anglelist)
    trajlist = csvread("Trajectories/%s.csv" % (trialnum, ))
    #TODO: add extra inputs to readtrajectories
    trajectories = readtrajectories(trajlist)
    #import pdb; pdb.set_trace()
    try:
        if angles['LeftStartFrame'] != trajectories['LeftStartFrame']:
            print("WARNING: angle and trajectory files are using different left strides in trial %s" % trialnum)
        if angles['RightStartFrame'] != trajectories['RightStartFrame']:
            print("WARNING: angle and trajectory files are using different right strides in trial %s" % trialnum)
    except KeyError:
        print("WARNING: strides have not been marked on both sides.")
    for n in ['Left','Right']:
        trajectories[n+'Clearance'] = minclearance(trajectories[n+'ToeZ'], trajectories[n+'StartFrame'], trajectories[n+'FoffFrame'], trajectories[n+'EndFrame'], 0.2, 0.2)   
        trajectories[n+'AnkleAngle'] = angles[n+'AnkleAngle']
    return trajectories

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
    for trial in trials:
        print("""Please enter the trial number for %s""" % (trial, ))
        trialnum = input()
        subject[trial] = onetrial(trialnum)
    afile = open(r'Subject%s.pkl' % (participant, ), 'wb')
    pickle.dump(subject, afile)
    afile.close()
