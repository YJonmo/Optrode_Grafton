"""
Demonstrates reading 2 analog inputs (AINs) in a loop from a LabJack.

"""

from labjack import ljm
import matplotlib.pyplot as plt
import numpy as np

import time

read_signal = np.zeros(100)

# Open first found LabJack
handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
#handle = ljm.openS("ANY", "ANY", "ANY")

info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n" \
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" % \
    (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

# Setup and call eWriteNames to configure AINs on the LabJack.
numFrames = 6
names = ["AIN0_NEGATIVE_CH", "AIN0_RANGE", "AIN0_RESOLUTION_INDEX",
         "AIN1_NEGATIVE_CH", "AIN1_RANGE", "AIN1_RESOLUTION_INDEX"]
aValues = [199, 2, 17,
           199, 10, 0]
ljm.eWriteNames(handle, numFrames, names, aValues)

print("\nSet configuration:")
for i in range(numFrames):
    print("    %s : %f" % (names[i], aValues[i]))

# Setup and call eReadNames to read AINs from the LabJack.
numFrames = 2
names = ["AIN0", "AIN1"]

print("\nStarting read loop.  Press Ctrl+C to stop.")
delay = .1 #delay between readings (in sec)
while True:
    try:
        results = ljm.eReadNames(handle, numFrames, names)
        read_signal[1:] = read_signal[0:99]   
        read_signal[0] = results[0]
        print("\nAIN0 : %f V, AIN1 : %f V" % (results[0], results[1]))
        plt.plot(read_signal)
        #plt.ion()
        #plt.show()
        #time.sleep(1)
        plt.pause(0.1)
        plt.clf()
        time.sleep(delay)
    except KeyboardInterrupt:
        break
    except Exception:
        import sys
        print(sys.exc_info()[1])
        break

# Close handle
ljm.close(handle)
