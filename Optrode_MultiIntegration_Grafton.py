import h5py
import DAQT7_Obj as DAQ
import SeaBreeze_Obj as SB
import time
import datetime
import numpy as np
from multiprocessing import Process, Pipe, Value, Array
from labjack import ljm
import SeaBreeze_Obj as SB
import matplotlib.pyplot as plt
import os.path
time_start =  time.time()


# ######################### Naming the DAQ ports ##########################
Green_Laser = "FIO1"
Green_Shutter = "FIO3"
Blue_Laser = "FIO0"
Blue_Shutter = "FIO2"
Green_Shutter_CloseDelay = 0.030  #Delay in seconds for the shutter to close as measured with testing
Blue_Shutter_CloseDelay  = 0.010  #Delay in seconds for the shutter to close as measured with testing

PhotoDiod_Port = "AIN0"
Spectrometer_Trigger_Port = "DAC0"


On = 1
Off = 0
Open = 1
Close = 0
Do_Trigger = 5
No_Trigger = 0
External_Edge = 3
Free_Running = 0

PhotoDiode_Threshold = 0.3                 #This threshold (in volts) defines the moment when the laser beam is detected via photodiode.
Command_Signal_Hight = 2.7                 #This value defines the value of the command signal at high and it should be similar to what is seen on photodiode when the beam is exposed, but is should be a value below 4.5 to avoid saturation
Command_signal_Low = 0                     #This value defines the value of the command signal at low and it should be similar to what is seen on photodiode when the beam is not exposed
# ####################### Interrupt like delays (s) #######################
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

# # A function for initializing the spectrometer (integration time and triggering mode
def SB_Init_Process(Spec_handle,Integration_time, Trigger_mode):
    SB.Init(Spec_handle,Integration_time, Trigger_mode)
    print 'Spectrometer is initialized'

# ########## A function for reading the spectrometer intensities ###########
def SB_Read_Process(Spec_handle):
    print 'Spectrumeter is waiting'
    Correct_dark_counts = True
    Correct_nonlinearity = True
    Intensities = SB.Read(Spec_handle, Correct_dark_counts, Correct_nonlinearity)
    SB_Current_Record[:] = Intensities
    SB_Is_Done.value = 1
    print "Intensities are read"
    return


# ######## A function for reading the DAQT7 analogue inpute on AINX. Input voltage can be from 0 to 10v ########
def DAQ_Read():
    results = DAQ.AIN_Read(DAQ_handle, PhotoDiod_Port)
    read_signal[DAC_Sampl_Index] = results[0]
    read_time = time.time()
    return results[0], read_time


if __name__ == "__main__":
    # ################# Detecting the spectrometer and the DAQ ###########
    Spec_handle = SB.Detect()
    DAQ_handle = DAQ.Init()
    # ############## Initializing the ports ##############
    DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, Off)
    DAQ.Digital_Ports_Write(DAQ_handle, Blue_Laser, On)       #Laser is on
    DAQ.Digital_Ports_Write(DAQ_handle, Green_Laser, On)       #Laser is on
    DAQ.Digital_Ports_Write(DAQ_handle, Green_Shutter, Off)       #Shutter is close
    DAQ.Digital_Ports_Write(DAQ_handle, Blue_Shutter, Off)       #Shutter is close


    while True:
        Current_Laser = raw_input('Which laser you want? Press G for green laser or press B for blue laser and then press Enter:')
        if (Current_Laser == 'G') | (Current_Laser == 'g'):
            Laser = Green_Laser
            Shutter = Green_Shutter
            Shutter_CloseDelay = Green_Shutter_CloseDelay
            break
        elif (Current_Laser == 'B') | (Current_Laser == 'b'):
            Laser = Blue_Laser
            Shutter = Blue_Shutter
            Shutter_CloseDelay = Blue_Shutter_CloseDelay
            break
        else:
            print 'Wrong input!, Try again'


    # ##################### Initializing the variables ###################
    #Integration_list = [8000, 16000, 32000, 64000, 128000, 256000, 512000, 1024000, 2048000]
    Integration_list_sec = [0.008, 0.016, 0.032, 0.064, 0.128, 0.256, 0.512 ]   # Integration list in seconds
    Integration_margin = 0.2                                        #(In seconds) This is the duration before the external edge trigger is given to the spectrometer while the specrumeter started the integration period
    Integration_OffSet = 0.005                                      # You need to play with this value to obtain an accurate integration period. By default it is 0.005 seconds. This is important on short integration periods
    #Integration_base = Integration_list_sec[-1]*1000000 + Integration_margin*2000000    # This is the integration time applied for all the trials
    Integration_base =  2*1000000    # This is the integration time applied for all the trials in microseconds
    No_DAC_Sample = 10000 # Number of samples for Photodiod per iteration of the laser exposer. Every sample takes ~0.6 ms.
    SB_Is_Done = Value('i', 0)                  #This bit checkes wheatehr the sepctrometer is finished reading
    SB_Current_Record = Array('d', np.zeros(shape=( len(Spec_handle.wavelengths()) ,1), dtype = float ))
    SB_Is_Done.value = 0
    Timer_Is_Done = Value('i', 0)               #This bit checkes wheatehr the time assigned to the timer is elapsed
    Timer_Is_Done.value = 0
    Timer_Is_Done2 = Value('i', 0)
    Timer_Is_Done2.value = 0
    SB_Full_Records = np.zeros(shape=(len(Spec_handle.wavelengths()), len(Integration_list_sec)+1 ), dtype = float )
    read_signal = np.zeros(No_DAC_Sample*len(Integration_list_sec))
    read_time   = np.zeros(No_DAC_Sample*len(Integration_list_sec))
    '''
    Open_delay = np.zeros(50)
    Close_delay = np.zeros(50)
    '''
    read_signal_ref = np.zeros(No_DAC_Sample*len(Integration_list_sec))
    read_time_ref   = np.zeros(No_DAC_Sample*len(Integration_list_sec))


    # ########### The file containing the records (HDF5 format)###########'''
    Path_to_Records = os.path.abspath(os.path.join( os.getcwd(), os.pardir)) + "/Records"
    os.chdir(Path_to_Records)
    #File_name = "water_4_" + str('%i' %time.time())+ ".hdf5"
    File_name = "water_4_" + str('%s' %datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S'))+ ".hdf5"
    #File_name = "Opterode_Recording_At" + str('%i' %time.time())+ ".hdf5"
    f = h5py.File(File_name, "w")
    Spec_sub1 = f.create_group("Spectrumeter")
    Spec_specification = Spec_sub1.create_dataset("Spectrumeter", (10,), dtype='f')
    Spec_specification.attrs['Serial Number'] = np.string_(Spec_handle.serial_number)
    Spec_specification.attrs['Model'] = np.string_(Spec_handle.model)
    Spec_wavelength = f.create_dataset('Spectrumeter/Wavelength', data = Spec_handle.wavelengths())

    #File_name = "Opterode_Recording_At" + str('%i' %time.time())+ ".hdf5"


    DAQ.Digital_Ports_Write(DAQ_handle, Laser, on)       #Laser is on
    P1 = Process(target=SB_Init_Process, args=(Spec_handle,Integration_base, External_Edge))
    P1.start()
    time.sleep(0.1)

    DAC_Sampl_Index = -1
    Integration_index = 0
    Spec_Sampl_Index = 0


    # ## The main loop for recording the spectrometer and the photodiod ##
    while Integration_index < len(Integration_list_sec):
        #Start_time = time.time()
        Timer_Is_Done.value = 0
        P_Timer = Process(target=Timer_Multi_Process, args=(Integration_margin,)) #  This margin is used to check if the QE65000 fails on staying for the integration period
        P_Timer.start()

        P2 = Process(target=SB_Read_Process, args=(Spec_handle,))
        P2.start()

        DAQ.Digital_Ports_Write(DAQ_handle, Laser, On)       #Laser is on
        DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, Do_Trigger)  # Spec is edge-triggered  and start ~20ms later to acquire
        time.sleep(0.01)
        DAQ.Digital_Ports_Write(DAQ_handle, Shutter, Close)
        time.sleep(0.01)
        Open_delay = time.time()

        while Timer_Is_Done.value == 0:
            DAC_Sampl_Index += 1
            read_signal_ref[DAC_Sampl_Index] = Command_Signal_Low
            read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()

        #print 'Elapsed time %f' %(time.time() - Start_time)
        Latch_Laser_Detect = 0


        #if SB_Is_Done.value == 1:
        #    print 'Eroooooooor'
        while SB_Is_Done.value == 1:                                    #Entering this loop means that the spectrometer failed to stay for the whole duration of the integration time. With QE65000 there is a 15% chance of enterinf to thos look. If this happens too often then reset the spectrometer
            SB_Is_Done.value = 0                                        #So spectrometer will be retriggered
            print 'Spectrometer Error, will retrigger the Spectrometer'
            DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, No_Trigger)
            time.sleep(0.01)
            P2 = Process(target=SB_Read_Process, args=(Spec_handle,))
            P2.start()
            DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, Do_Trigger)  # Spec is edge-triggered  and start ~20ms later to acquire
            time.sleep(0.04)


        Timer_Is_Done.value = 0
        P_Timer = Process(target=Timer_Multi_Process, args=(Integration_base/float(1000000) - Integration_margin*2 - Integration_list_sec[Integration_index],)) # keep the laser on before opening the shutter
        P_Timer.start()
        while Timer_Is_Done.value == 0:
            DAC_Sampl_Index += 1
            read_signal_ref[DAC_Sampl_Index] = Command_Signal_Low
            read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()

        DAQ.Digital_Ports_Write(DAQ_handle, Shutter, Open)       #Shutter opens in ~9ms since now
        #time.sleep(0.02)
        CurrentDelay = Integration_list_sec[Integration_index] - Integration_OffSet
        while SB_Is_Done.value == 0:
            DAC_Sampl_Index += 1
            read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
            read_signal_ref[DAC_Sampl_Index] = Command_Signal_Low
            if  (Latch_Laser_Detect == 0) & (read_signal[DAC_Sampl_Index] > PhotoDiode_Threshold):
                #State = Command_Signal_Hight
                #print CurrentDelay
                Timer_Is_Done.value = 0
                P_Timer = Process(target=Timer_Multi_Process, args=(CurrentDelay,)) # keep the laser on before opening the shutter
                P_Timer.start()
                Latch_Laser_Detect = 1

                while Timer_Is_Done.value == 0:
                    #print 'step 3'
                    DAC_Sampl_Index += 1
                    read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
                    read_signal_ref[DAC_Sampl_Index] = Command_Signal_Hight
                #State = Command_signal_Low
                DAQ.Digital_Ports_Write(DAQ_handle, Laser, Off)       #Laser is off

                DAC_Sampl_Index += 1
                read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
                read_signal_ref[DAC_Sampl_Index] = Command_signal_Low

                DAQ.Digital_Ports_Write(DAQ_handle, Shutter, Close)       #Shutter closes in ~9ms since now

                P_Timer2 = Process(target=Timer_Multi_Process2, args=(Shutter_CloseDelay,)) # keep the laser on before opening the shutter
                P_Timer2.start()
                while Timer_Is_Done2.value == 0:
                    #print 'step 3'
                    DAC_Sampl_Index += 1
                    read_signal[DAC_Sampl_Index], read_time[DAC_Sampl_Index] = DAQ_Read()
                    read_signal_ref[DAC_Sampl_Index] = Command_signal_Low
                Timer_Is_Done2.value = 0
                #time.sleep(0.030)
                DAQ.Digital_Ports_Write(DAQ_handle, Laser, On)       #Laser is on
                #Open_delay[Shutter_Open_Delay_Index] = time.time() - Open_time


            #read_time_ref[DAC_Sampl_Index] = time.time()
            #read_signal_ref[DAC_Sampl_Index] = Command_State
        SB_Full_Records[:,Spec_Sampl_Index] = SB_Current_Record[:]
        Spec_Sampl_Index += 1

        Integration_index += 1
        print "The whole integration cycle: %f" % (time.time() - Open_delay)
        SB_Is_Done.value = 0
        Timer_Is_Done.value = 0


    DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, No_Trigger)
    time.sleep(0.01)
    P2 = Process(target=SB_Read_Process, args=(Spec_handle,))
    P2.start()
    time.sleep(0.01)
    DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, Do_Trigger)  # Spec is edge-triggered  and start ~20ms later to acquire
    time.sleep(0.05)
    while SB_Is_Done.value == 1:
        SB_Is_Done.value = 0
        print 'Spectrometer Error, will retrigger the Spectrometer'
        DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, No_Trigger)
        time.sleep(0.01)
        P2 = Process(target=SB_Read_Process, args=(Spec_handle,))
        P2.start()
        DAQ.DAC_Write(DAQ_handle, Spectrometer_Trigger_Port, Do_Trigger)  # Spec is edge-triggered  and start ~20ms later to acquire
        time.sleep(0.05)
    while SB_Is_Done.value == 0:
        time.sleep(0.1)
        #print 'BackGround'
    SB_Full_Records[:,Spec_Sampl_Index] = SB_Current_Record[:]






    DAQ.Digital_Ports_Write(DAQ_handle, Laser, On)       #Laser stays on
    # ########### Saving the recorded signals in HDF5 format ############ '''
    read_signal2 = np.zeros(DAC_Sampl_Index)
    read_time2   = np.zeros(DAC_Sampl_Index)
    read_signal_ref2 = np.zeros(DAC_Sampl_Index)
    read_signal2[:] = read_signal[0:DAC_Sampl_Index]
    read_time2[:] = read_time[0:DAC_Sampl_Index]
    read_signal_ref2[:] = read_signal_ref[0:DAC_Sampl_Index]

    Spec_intensities = f.create_dataset('Spectrumeter/Intensities', data = SB_Full_Records)
    Spec_intensities = f.create_dataset('DAQT7/DAC_Readings', data = read_signal2)
    Spec_intensities = f.create_dataset('DAQT7/DAC_Time_Stamps', data = read_time2)
    Spec_intensities = f.create_dataset('DAQT7/DAC_Command_Signal', data = read_signal_ref2)
    f.close()


    Path_to_Fred_Codes = os.path.abspath(os.path.join( os.getcwd(), os.pardir)) + "/Fred"
    os.chdir(Path_to_Fred_Codes)

    SB.Close(Spec_handle)
    #DAQ.Close(DAQ_handle)
    # ######### Plotting the spectrumeter and the photodiod recordings ########
    plt.figure()
    read_time_index = read_time2 - read_time2[0]
    read_time_index_ref2 = read_time_ref - read_time_ref[0]
    plt.plot(read_time_index,read_signal2, label = "Photo Diode")
    plt.plot(read_time_index,read_signal_ref2, label = "Command Signal")
    plt.legend( loc='upper left', numpoints = 1 )
   #plt.legend('PhotoDiode', 'CommandSignal')
    plt.title('Photo diode')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (v)')
    plt.pause(1)

    plt.figure()
    plt.plot(Spec_handle.wavelengths()[1:],SB_Full_Records[1:])
    plt.title('Specrometer recordings')
    plt.xlabel('Wavelength (nano meter)')
    plt.ylabel('Intensity')
    plt.pause(0.1)
