
import numpy as np
import time
import seabreeze.spectrometers as sb


''' ************** Detection of the Spectrumeter OceanOptics **************** '''
def Detect ():
    devices = sb.list_devices()
    print devices
    spec = sb.Spectrometer(devices[0])
    print 'Serial number:%s' % spec.serial_number
    print 'Model:%s' % spec.model
    print 'minimum_integration_time_micros: %s microseconds' % spec.minimum_integration_time_micros
    
    spec.trigger_mode(0)            #Flushing the stuff down and make the spectrometer ready for the next steps!
    spec.integration_time_micros(10000)
    spec.wavelengths()
    Intensities = spec.intensities(correct_dark_counts=True, correct_nonlinearity=True)
    Intensities = spec.intensities(correct_dark_counts=True, correct_nonlinearity=True)
    Intensities = spec.intensities(correct_dark_counts=True, correct_nonlinearity=True)
    Intensities = spec.intensities(correct_dark_counts=True, correct_nonlinearity=True)
    return spec


''' Initialization for the inegration time and the trigger mode. 
HR2000+, USB2000+and Flame-S Set Trigger Mode 

Data Value = 0 ==> Normal (Free running) Mode
Data Value = 1 ==> Software Trigger Mode
Data Value = 2 ==> External Hardware Level Trigger Mode
Data Value = 3 ==> External Synchronization Trigger Mode
Data Value = 4 ==> External Hardware Edge Trigger Mode


HR4000, USB4000 and Flame-T Set Trigger Mode

Data Value = 0 ==> Normal (Free running) Mode
Data Value = 1 ==> Software Trigger Mode
Data Value = 2 ==> External Hardware Level Trigger Mode
Data Value = 3 ==> Normal (Shutter) Mode 
Data Value = 4 ==> External Hardware Edge Trigger Mode


Maya2000Pro and Maya - LSL, QE65000, QE65 Pro, and QE Pro Set Trigger Mode

Data Value = 0 ==> Normal (Free running) Mode
Data Value = 1 ==> External Hardware Level Trigger Mode
Data Value = 2 ==> External Synchronous Trigger Mode*
Data Value = 3 ==> External Hardware Edge Trigger Mode
*Not yet implemented on the QE Pro


NIRQuest Set Trigger Mode

Data Value = 0 ==> Normal (Free running) Mode
Data Value = 3 ==> External Hardware Edge Trigger Mode
'''
def Init(spec,Integration_time, Trigger_mode):
    spec.trigger_mode(Trigger_mode)
    time.sleep(0.01)
    #spec.integration_time_micros(10000)
    spec.integration_time_micros(Integration_time)
    return


''' Reading the intensities.
Important! the first element in the Intensities array is the unix time for when the reading is finished.
''' 
def Read(spec,Correct_dark_counts, Correct_nonlinearity):
    Intensities = spec.intensities(correct_dark_counts=Correct_dark_counts, correct_nonlinearity=Correct_nonlinearity)
    #Intensities[0] = np.float(time.time())    
    Intensities[0] = int(round(time.time() * 1000)) 
    #print Intensities[0]   
    return Intensities


''' Closing the device '''
def Close(spec):
    spec.close()
    