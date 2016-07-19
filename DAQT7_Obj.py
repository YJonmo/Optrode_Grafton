"""
Demonstrates reading 2 analog inputs (AINs) in a loop from a LabJack.

"""
from labjack import ljm
#import matplotlib.pyplot as plt
#import numpy as np
#import time



''' 
Initialization and detection of the LabJack device
'''
def Init():                 
    # Open first found LabJack
    handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
    #handle = ljm.openS("ANY", "ANY", "ANY")
    #A2D setup
    info = ljm.getHandleInfo(handle)
    print("Opened a LabJack with Device type: %i, Connection type: %i,\n" \
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" % \
    (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))
    # Setup and call eWriteNames to configure AINs on the LabJack.
    numFrames = 3
    names = ["AIN_ALL_NEGATIVE_CH", "AIN_ALL_RANGE", "AIN_ALL_RESOLUTION_INDEX"]
    aValues = [199, 10, 1]
    ljm.eWriteNames(handle, numFrames, names, aValues)
    #return handle, Info
    return handle
 

''' 
Writing analogue values (0 to 5 v) in the DAC ports
'''
def DAC_Write(handle,DAC, Volt): # Volt is an integer (e.g., can be used for clossing or openning Shutter: 0=close, 5=open)
                                 # This can also be used for digital ports e.g.: DAC_Write(DAQ_handle, 'FIO0', 1) brings the port FIO0 to 3 v 
    ljm.eWriteName(handle, DAC, Volt)
    #print int(round(time.time() * 1000))
    return


''' 
Reading analogue inpute values (0 to 10 v) in the AIN ports. 
To change the range of input voltage or speed of conversion, below lines should be changed in the intialization:
numFrames = 3
names = ["AIN0_NEGATIVE_CH", "AIN0_RANGE", "AIN0_RESOLUTION_INDEX"]
aValues = [199, 2, 1]
ljm.eWriteNames(handle, numFrames, names, aValues) 
'''
def AIN_Read(handle,AIN): 
    return ljm.eReadNames(handle,1 , [AIN])


'''
Writing 1 or 0 in the digital ports. Digital port will 3.3v if State = 1 and 0v if State = 0. 
'''
def Digital_Ports_Write(handle,Port,State):     
    ljm.eWriteName(handle, Port, State)
    #print int(round(time.time() * 1000))
    return

'''
Reading the State of the digital ports.  
'''
def Digital_Ports_Read(handle,Port): 
    return ljm.eReadName(handle, Port)
    

'''
Closing the device
'''
def Close(handle):
    ljm.close(handle)
