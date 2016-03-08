import h5py
import DAQT7_Obj as DAQ
import SeaBreeze_Obj as SB
import time
import numpy as np
from multiprocessing import Process, Pipe, Value, Array
from labjack import ljm
import SeaBreeze_Obj as SB
import matplotlib.pyplot as plt
import os.path
time_start =  time.time()


# ######################### Naming the DAQ ports ##########################
# FIO0 = shutter of the green laser and FIO1 is the shutter of the blue laser
# FIO2 = is the green laser and the FIO3 is the blue laser
#
Green_Laser = "FIO1"
Green_Shutter = "FIO3"
Blue_Laser = "FIO0"
Blue_Shutter = "FIO2"

#Laser_Port = Blue_Laser
#Shutter_Port = Shutter_Blue
PhotoDiod_Port = "AIN0"
Spectrometer_Trigger_Port = "DAC0"

# ####################### Interrupt like delays (s) ####################### '''
# Usage Ex: Px = Process(target=Timer_Multi_Process, args=(Timer_time,))
# Px.start() and in your code constantly check for "Timer_Is_Done"

def Timer_Multi_Process(Time_In_Seconds):
    if Timer_Is_Done.value is 1:
        print 'Error: This timer can be run one at a time. Either the previous timer is still running, or Timer_Is_Done bit is reset from previous timer run'
    time.sleep(Time_In_Seconds)
    Timer_Is_Done.value = 1

def Timer_Multi_Process2(Time_In_Seconds):
    if Timer_Is_Done2.value is 1:
        print 'Error: This timer can be run one at a time. Either the previous timer is still running, or Timer_Is_Done bit is reset from previous timer run'
    time.sleep(Time_In_Seconds)
    Timer_Is_Done2.value = 1

# # A function for initializing the spectrometer (integration time and triggering mode '''
def SB_Init_Process(Spec_handle,Integration_time, Trigger_mode):
    print 'Spectrometer is initialized'
    SB.Init(Spec_handle,Integration_time, Trigger_mode)


# ########## A function for reading the spectrometer intensities ########### '''
def SB_Read_Process(Spec_handle):

    #print 'Spectrumeter is waiting'
    Correct_dark_counts = True
    Correct_nonlinearity = True
    Intensities = SB.Read(Spec_handle, Correct_dark_counts, Correct_nonlinearity)
    #print Intensities
    SB_Current_Record[:] = Intensities
    #SB_Current_Record[0] = np.float(time.time())
    SB_Is_Done.value = 1
    #print "Intensities are read"
    return


# ######## A function for reading the DAQ analogue inpute on AINX ########
def DAQ_Read():
    results = DAQ.AIN_Read(DAQ_handle, PhotoDiod_Port)
    read_signal[DAC_Sampl_Index] = results[0]
    read_time = time.time()
    return results[0], read_time


if __name__ == "__main__":
    # ################# Detecting the spectrometer and the DAQ ###########
    Spec_handle = SB.Detect()
    DAQ_handle = DAQ.Init()
    # ############## All the ports are off at the beginning ##############
    DAQ.Digital_Ports_Write(DAQ_handle, 'FIO0', 0)
    DAQ.Digital_Ports_Write(DAQ_handle, 'FIO1', 0)
    DAQ.Digital_Ports_Write(DAQ_handle, 'FIO2', 0)
    DAQ.Digital_Ports_Write(DAQ_handle, 'FIO3', 0)
    DAQ.DAC_Write(DAQ_handle, 'DAC0', 0)
    DAQ.DAC_Write(DAQ_handle, 'DAC1', 0)
    DAQ.Digital_Ports_Write(DAQ_handle, Blue_Laser, 1)       #Laser is on
    DAQ.Digital_Ports_Write(DAQ_handle, Green_Laser, 1)       #Laser is on
    DAQ.Digital_Ports_Write(DAQ_handle, Green_Shutter, 0)       #Shutter is close
    DAQ.Digital_Ports_Write(DAQ_handle, Blue_Shutter, 0)       #Shutter is close


    while 1==1:
        Current_Laser = raw_input('Which laser you want? Press G for green laser or press B for blue laser and then press Enter:')
        if (Current_Laser == 'G') | (Current_Laser == 'g'):
            Laser_Port = Green_Laser
            Shutter_Port = Green_Shutter
            break
        elif (Current_Laser == 'B') | (Current_Laser == 'b'):
            Laser_Port = Blue_Laser
            Shutter_Port = Blue_Shutter
            break
        else:
            print 'Wrong input!'

    # ##################### Initializing the variables ###################
    #Integration_list = [8000, 16000, 32000, 64000, 128000, 256000, 512000, 1024000, 2048000]
    #Integration_list_sec = [0.008, 0.016, 0.032, 0.064, 0.128, 0.256, 0.512, 1.024, 2.048]
    Integration_marging = 0.3                                        #(In seconds) This is the duration before the external edge trigger is given to the spectrometer while the specrumeter started the integration period
    No_Spec_Sample = 100
    #Integration_base = Integration_list_sec[-1]*1000000 + Integration_marging*2000000    # This is the integration time applied for all the trials
    Integration_base = 32000
    No_DAC_Sample = 10000 # Number of samples for Photodiod per iteration of the laser exposer. Every sample takes ~0.6 ms.
    SB_Is_Done = Value('i', 0)
    SB_Current_Record = Array('d', np.zeros(shape=( len(Spec_handle.wavelengths()) ,1), dtype = float ))
    SB_Is_Done.value = 0
    Timer_Is_Done = Value('i', 0)
    Timer_Is_Done.value = 0
    Timer_Is_Done2 = Value('i', 0)
    Timer_Is_Done2.value = 0
    SB_Full_Records = np.zeros(shape=(len(Spec_handle.wavelengths()),  No_Spec_Sample), dtype = float )
    read_signal = np.zeros(No_DAC_Sample*Integration_base)
    read_time   = np.zeros(No_DAC_Sample*Integration_base)


    # ########### The file containing the records (HDF5 format)###########'''
    Path_to_Records = os.path.abspath(os.path.join( os.getcwd(), os.pardir)) + "/Records"
    os.chdir(Path_to_Records)
    File_name = time.strftime('%Y%m%d%H%M%S')+"_" + "powermeter_10_01" + ".hdf5"
    #"473nm_power_meas" + str('%i' %time.time())+ ".hdf5"
    #File_name = "Opterode_Recording_At" + str('%i' %time.time())+ ".hdf5"
    f = h5py.File(File_name, "w")
    Spec_sub1 = f.create_group("Spectrumeter")
    Spec_specification = Spec_sub1.create_dataset("Spectrumeter", (10,), dtype='f')
    Spec_specification.attrs['Serial Number'] = np.string_(Spec_handle.serial_number)
    Spec_specification.attrs['Model'] = np.string_(Spec_handle.model)
    Spec_wavelength = f.create_dataset('Spectrumeter/Wavelength', data = Spec_handle.wavelengths())


    Path_to_Fred_Codes = os.path.abspath(os.path.join( os.getcwd(), os.pardir)) + "/Fred"
    os.chdir(Path_to_Fred_Codes)


    Spec_Integration_Time = 20000                       # Integration time for free running mode
    P1 = Process(target=SB_Init_Process, args=(Spec_handle,Spec_Integration_Time,0))
    P1.start()
    time.sleep(0.1)
    P1 = Process(target=SB_Init_Process, args=(Spec_handle,Spec_Integration_Time,0))
    P1.start()
    time.sleep(0.1)
    P1 = Process(target=SB_Init_Process, args=(Spec_handle,Spec_Integration_Time,0))
    P1.start()
    time.sleep(0.1)

    State = 0

    DAC_Sampl_Index = -1
    Integration_index = 0
    Spec_Sampl_Index = 0


    # ## The main loop for recording the spectrometer and the photodiod ##
    P_Timer = Process(target=Timer_Multi_Process, args=(0.1,)) # keep the laser on before opening the shutter
    P_Timer.start()
    while Timer_Is_Done.value == 0:
        DAC_Sampl_Index += 1
        read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
    Timer_Is_Done.value = 0



    DAQ.Digital_Ports_Write(DAQ_handle, Shutter_Port, 1)
    P_Timer = Process(target=Timer_Multi_Process, args=(10.1,)) # keep the laser on before opening the shutter
    P_Timer.start()
    while Timer_Is_Done.value == 0:
        P_Timer2 = Process(target=Timer_Multi_Process2, args=(2.00,)) # keep the laser on before opening the shutter
        P_Timer2.start()
        DAQ.Digital_Ports_Write(DAQ_handle, Laser_Port, 1)
        while Timer_Is_Done2.value == 0:
            DAC_Sampl_Index += 1
            read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
        Timer_Is_Done2.value = 0

        P_Timer2 = Process(target=Timer_Multi_Process2, args=(0.01,)) # keep the laser on before opening the shutter
        P_Timer2.start()
        DAQ.Digital_Ports_Write(DAQ_handle, Laser_Port, 0)  #Turn the laser on right after first intergration is over, and start recording
        while Timer_Is_Done2.value == 0:
            DAC_Sampl_Index += 1
            read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
        Timer_Is_Done2.value = 0

    Timer_Is_Done.value = 0





        #print (time.time() - Start_time)


    DAQ.Digital_Ports_Write(DAQ_handle, Laser_Port, 1)
    DAQ.Digital_Ports_Write(DAQ_handle, Shutter_Port, 0)


    DAQ.Digital_Ports_Write(DAQ_handle, Laser_Port, 1)





    # ########### Saving the recorded signals in HDF5 format ############
    read_signal2 = np.zeros(DAC_Sampl_Index)
    read_time2   = np.zeros(DAC_Sampl_Index)
    read_signal2[:] = read_signal[0:DAC_Sampl_Index]
    read_time2[:] = read_time[0:DAC_Sampl_Index]

    Spec_intensities = f.create_dataset('Spectrometer/Intensities', data = SB_Full_Records)
    Spec_intensities = f.create_dataset('DAQT7/DAC_Readings', data = read_signal2)
    Spec_intensities = f.create_dataset('DAQT7/DAC_Time_Stamps', data = read_time2)
    f.close()


    print 'File %s is saved in %s' %(File_name ,  Path_to_Records)

    Path_to_Fred_Codes = os.path.abspath(os.path.join( os.getcwd(), os.pardir)) + "/Fred"
    os.chdir(Path_to_Fred_Codes)


    #DAQ.Close(DAQ_handle)
    # ######### Plotting the spectrumeter and the photodiod recordings ########
    plt.figure()
    read_time_index = read_time2 - read_time2[0]
    plt.plot(read_time_index,read_signal2, label = "Photo Diode")
    #plt.legend( loc='upper left', numpoints = 1 )
   #plt.legend('PhotoDiode', 'CommandSignal')
    plt.title('Photo diode')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (v)')
    plt.pause(.1)

    plt.figure()
    plt.plot(Spec_handle.wavelengths()[1:],SB_Full_Records[1:])
    plt.title('Specrometer recordings')
    plt.xlabel('Wavelength (nano meter)')
    plt.ylabel('Intensity')
    plt.pause(.1)

    plt.figure()
    Spec_Delay = np.zeros(No_Spec_Sample)
    for I in range(No_Spec_Sample-1):
        Spec_Delay[I] = (SB_Full_Records[0,I+1]-SB_Full_Records[0,I])
    plt.plot(Spec_Delay)
    plt.title('Delay of each read iteration')
    plt.xlabel('Iterations index')
    plt.ylabel('Time (ms)')
    plt.pause(.1)
    SB.Close(Spec_handle)

