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
    
def readtrajectories(filelist):
    """
    Read a numpy array object in Vicon export format with marker trajectories.
    Output is a dictionary with the following parts:-
    LeftSpeed/RightSpeed = walking speed
    LeftFoff/RightFoff = foot off %
    LeftFoffFrame/RightFoffFrame = frame of foot off in marked stride
    LeftStartFrame/RightStartFrame = frame of initial footstrikes in marked stride
    LeftEndFrame/RightEndFrame = frame of final footstrikes in marked stride
    LeftStepLen/RightStepLen = step length in marked stride
    LeftToeZ/RightToeZ = vector of toe marker Z coord throughout trial
    """
    filelen = len(filelist) - 2
    trajstart = filelen
    output = {}
    LtoeZ = []
    RtoeZ = []
    for n in range(filelen):
        try:
            # Assign gait parameters to dictionary
            if filelist[n][0] == 'Trajectories':
                trajstart = n + 5
            elif filelist[n][2] == 'Walking Speed':
                output[filelist[n][1]+'Speed'] = float(filelist[n][3])
            elif filelist[n][2] == 'Foot Off':
                if filelist[n][1]+'Foff' not in output:
                    output[filelist[n][1]+'Foff'] = float(filelist[n][3])
                elif filelist[n][1]+'FoffFrame' not in output:
                    output[filelist[n][1]+'FoffFrame'] = int(float(filelist[n][3]) * 100)
            elif filelist[n][2] == 'Step Length':
                output[filelist[n][1]+'StepLen'] = float(filelist[n][3])
            elif filelist[n][2] == 'Foot Strike':
                # First instance of foot strike is StartFrame. 
                # Convert seconds to frames at 100Hz.
                if filelist[n][1]+'StartFrame' not in output:
                    output[filelist[n][1]+'StartFrame'] = int(float(filelist[n][3]) * 100)
                else:
                    output[filelist[n][1]+'EndFrame'] = int(float(filelist[n][3]) * 100)
            elif n >= trajstart:
                LtoeZ.append(filelist[n][31])
                RtoeZ.append(filelist[n][49])
        except IndexError:
            continue
    output['LeftToeZ'] = [('0' if n=='' else float(n)) for n in LtoeZ]
    output['RightToeZ'] = [('0' if n=='' else float(n)) for n in RtoeZ]
    #import pdb; pdb.set_trace()
    return output
    
def readangles(filelist):
    """
    Read a numpy array object in Vicon export format with model outputs.
    Output is a dictionary with the following parts:-
    LeftStartFrame/RightStartFrame = frame of initial footstrikes in marked stride
    LeftEndFrame/RightEndFrame = frame of final footstrikes in marked stride
    LeftAnkleAngle/RightAnkleAngle = list of absolute ankle angles throughout trial
    """
    filelen = len(filelist) - 2
    output = {}
    anglestart = filelen
    Rankle = []
    Lankle = []
    for n in range(filelen):
        try:
            if filelist[n][0] == 'Model Outputs':
                anglestart = n + 5
            elif filelist[n][2] == 'Foot Strike':
                if filelist[n][1]+'StartFrame' not in output:
                    output[filelist[n][1]+'StartFrame'] = int(float(filelist[n][3]) * 100)
                else:
                    output[filelist[n][1]+'EndFrame'] = int(float(filelist[n][3]) * 100)
            elif n >= anglestart:
                # List ankle abs angles, convert to float if possible
                try:
                    Lankle.append(float(filelist[n][2]))
                except ValueError:
                    Lankle.append(filelist[n][2])
                try:
                    Rankle.append(float(filelist[n][101]))
                except ValueError:
                    Rankle.append(filelist[n][101])
        except IndexError:
            continue
    #import pdb; pdb.set_trace()
    output['LeftAnkleAngle'] = Lankle
    output['RightAnkleAngle'] = Rankle
    return output

def onetrial(trialnum):
    """
    Read in files for a single trial, extract useful information.
    """
    anglelist = csvread("Angles/%s.csv" % (trialnum, ))
    angles = readangles(anglelist)
    trajlist = csvread("Trajectories/%s.csv" % (trialnum, ))
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
    trials = ['OWN','FACTORY','R0','R50','R100','R150','R200','R300','X0','X50','X100','X150','X200','X300','D0','D50','D100','D150']
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
