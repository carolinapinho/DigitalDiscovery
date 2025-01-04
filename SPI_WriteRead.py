'''
Script made to control SPI communication with digilent Digital Discovery device. Specified for the pourpouse of ***** project
Windows application
22/10/2024 
Carolina Pinho
'''

from ctypes import *
import math
import sys
import argparse
import time
import numpy


def Configure_SPI(dwf,hdwf,args):
    print("Configuring SPI...")
    dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(1)) 

    filterAverage=c_uint32()
    idxCS = 0 # DIO-24
    idxClk = 1 # DIO-25 
    dwf.FDwfDigitalSpiFrequencySet(hdwf, c_double(args.FreqHz))
    dwf.FDwfDigitalSpiClockSet(hdwf, c_int(idxClk))  #clock set
    dwf.FDwfDigitalSpiDataSet(hdwf, c_int(0), c_int(2)) # 0 DQ0_MOSI_SISO = DIO-2 Digital Discovery DIO-26
    dwf.FDwfDigitalSpiDataSet(hdwf, c_int(1), c_int(3)) # 1 DQ1_MISO = DIO-3     Digital Discovery DIO-27
    dwf.FDwfDigitalSpiIdleSet(hdwf, c_int(0), c_int(3)) # 0 DQ0_MOSI_SISO = DwfDigitalOutIdleZet
    dwf.FDwfDigitalSpiIdleSet(hdwf, c_int(1), c_int(3)) # 1 DQ1_MISO = DwfDigitalOutIdleZet
    dwf.FDwfDigitalSpiModeSet(hdwf, c_int(args.mode))
    dwf.FDwfDigitalSpiOrderSet(hdwf, c_int(args.FirstBit)) # 1 MSB first
    
    dwf.FDwfDigitalInTriggerSet(hdwf, c_int(0), c_int(0), c_int(1<<0), c_int(0)) # DIO0/DIN0 rising edge

    dwf.FDwfDigitalSpiSelectSet(hdwf, c_int(idxCS), c_int(1)) # CS: DIO-0, idle high
    dwf.FDwfDigitalSpiWriteOne(hdwf, c_int(1), c_int(0), c_int(0)) # start driving the channels, clock and data
    dwf.FDwfDigitalSpiSelect(hdwf, c_int(idxCS),c_int(1))
def SPI_Write(dwf,hdwf,args):
    int_list = [int(x, 16) for x in args.data.split(',')]

    rgbTX =  (c_ubyte * len(int_list))(*int_list)
    
    rgbRX = (c_ubyte*len(int_list))()

    dwf.FDwfDigitalSpiReadOne(hdwf, c_int(1), c_int(8),rgbRX) # start driving the channels, clock and data

# cDQ 1 MOSI/MISO, 8bit words, MOSI words, MISO words
    #dwf.FDwfDigitalSpiRead(hdwf, c_int(1), c_int(8), rgbRX, c_int(len(rgbRX))) # read array of 8 bit (byte) length elements
    dwf.FDwfDigitalSpiWriteRead(hdwf, c_int(1), c_int(8), rgbTX, c_int(len(rgbTX)), rgbRX, c_int(len(rgbRX))) 

    print("TX: "+str(numpy.fromiter(rgbTX, dtype = numpy.uint8)))
    print("RX: "+str(numpy.fromiter(rgbRX, dtype = numpy.uint8)))
    print("Return (Hex): " + ', '.join(format(x, '02X') for x in rgbRX))

   
def main():
    parser = argparse.ArgumentParser(description="Script fo SPI Communication. Return the readed output of the write funciton. Should be the same data as the input in Hex ")
    parser.add_argument("--mode", type=int, default=3, help="Mode for SPI (0,1,2,3) \nMode	CPOL	CPHA\n 0	   0	    0\r 1	    0	    1\n2	    1	    0\n3	   1	    1")
    parser.add_argument("--data", type=str, help="Data to transfer in Hex. the expected format for the write operation \"40,82,00,00,00,00\" ")
    parser.add_argument("--FirstBit", type=int,default=1, help="1 MSB first or 0 LSB first", required=False)
    parser.add_argument("--FreqHz", type=int,default=8e6, help="Frequency for the SPI comm (default 8000000Hz) in Hz", required=False)
    args = parser.parse_args()
    if args.mode not in [0,1,2,3]:
        print("Erro! Por favor, forneça um modo válido. (0,1,2,3)")
        sys.exit()
    else:
        print(f'Using MODE, {args.mode}!')
    print(f'DATA, {args.data}!')
    #For the DigitalOut and IO functions, and AnalogIO DIOPP/PE the indexing 15:0 refers to DIO39:24. 
    if sys.platform.startswith("win"):
        dwf = cdll.LoadLibrary("dwf.dll")

    hdwf = c_int()

    print("Opening first device")
    dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))
    # device configuration of index 3 (4th) for Analog Discovery has 16kS digital-in/out buffer
    # dwf.FDwfDeviceConfigOpen(c_int(-1), c_int(3), byref(hdwf)) 
    if hdwf.value == 0:
        print("Failed to open device")
        szerr = create_string_buffer(512)
        dwf.FDwfGetLastErrorMsg(szerr)
        print(str(szerr.value))
        sys.exit()
    Configure_SPI(dwf,hdwf,args)
    SPI_Write(dwf,hdwf,args)
    dwf.FDwfDeviceCloseAll()
if __name__ == "__main__":
    main()