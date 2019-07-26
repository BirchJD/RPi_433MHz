#!/usr/bin/python

# Pi433MHz - 433MHz Data Reciever and Decoder
# Copyright (C) 2019 Jason Birch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#/****************************************************************************/
#/* Pi433MHz - 433MHz Data Reciever and Decoder.                             */
#/* ------------------------------------------------------------------------ */
#/* V1.00 - 2019-07-21 - Jason Birch                                         */
#/* ------------------------------------------------------------------------ */
#/* Script for monitoring a 433MHz and displaying packets of data received.  */
#/****************************************************************************/



import os
import sys
import math
import time
import datetime
import RPi.GPIO



# GPIO Pin connected to 433MHz receiver.
GPIO_RX_PIN = 26
# GPIO Pin connected to 433MHz transmitter (possible future experiments).
GPIO_TX_PIN = 19

# Put bad data lines in log file.
LOG_BAD_DATA = False

# When converting 5V signal to 3V3 signal for Raspberry Pi GPIO, NPN transistor inverts the signal.
RX_BIT_INVERT = 1
# Period of no RX data to consider end of RX data message.
RX_END_PERIOD = 0.25
# Smallest period of high or low signal to consider noise rather than data, and flag as bad data. 
RX_REJECT_PERIOD = 0.000025
# Ignore extra bits at start of transmission.
RX_START_BITS = 1
# RX Signature size, number of hex values to use as a signature.
RX_SIGNATURE_SIZE = 4

# RX data field names.
DATA_SEQUENCE = 0
DATA_RX_PIN = 1
DATA_LEVEL = 2
DATA_PERIOD = 3



class RxPacket:
   StartBitCount = RX_START_BITS
   AltStartBitCount = RX_START_BITS
   DataCount = 0
   Data = []
   BitPeriod = 0
   LastGpioLevel = RX_BIT_INVERT
   RxSignatures = {}



# Initialise application data.
def DataInit(ThisRxPacket):
   ThisRxPacket.StartBitCount = RX_START_BITS
   ThisRxPacket.AltStartBitCount = RX_START_BITS
   ThisRxPacket.DataCount = 0
   ThisRxPacket.Data = []
   ThisRxPacket.BitPeriod = 0
   ThisRxPacket.LastGpioLevel = RX_BIT_INVERT



# Write a line to the log file.
def WriteLogLine(LogFile, LogLine):
   sys.stdout.write(LogLine)
   LogFile.write(LogLine)


#  /*******************************************/
# /* Configure Raspberry Pi GPIO interfaces. */
#/*******************************************/
RPi.GPIO.setwarnings(False)
RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(GPIO_RX_PIN, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

# Initialise a new data packet capture.
ThisRxPacket = RxPacket
DataInit(ThisRxPacket)

# Infinate loop for this application.
ExitFlag = False
sys.stdout.write("\nWAITING FOR DATA...\n\n")
sys.stdout.flush()
while ExitFlag == False:
   # Check if data is currently being received.
   ThisPeriod = time.time()
   DiffPeriod = ThisPeriod - ThisRxPacket.BitPeriod
   if len(ThisRxPacket.Data) == 0 or DiffPeriod < RX_END_PERIOD:
      # If data level changes, log information about the data received, to be decoded when the RX data is complete.
      GpioLevel = RPi.GPIO.input(GPIO_RX_PIN)
      if GpioLevel != ThisRxPacket.LastGpioLevel:
         ThisRxPacket.Data.append([ThisRxPacket.DataCount, GPIO_RX_PIN, ThisRxPacket.LastGpioLevel, DiffPeriod])
         ThisRxPacket.DataCount += 1
         ThisRxPacket.BitPeriod = ThisPeriod
         ThisRxPacket.LastGpioLevel = GpioLevel
   else:
      # New log entry.
      LogEntry = ""
      BadDataFlag = False

      # End of data detected, decode data.
      Now = datetime.datetime.now()

      # Log the date and time of the RX data.
      LogEntry += Now.strftime("%Y-%m-%d %H:%M:%S\n")

      # Calculate the data size once, for use later.
      DataSize = len(ThisRxPacket.Data)
      LogEntry += "DATA SIZE: {:d} ".format(DataSize)

      # Itterate though the data to find the smallest period for a high level and smallest period for a low level.
      # This will be considered the TX data rate for high and low signals.
      MinLowPeriodSeqCount = 0
      MinLowPeriod = RX_END_PERIOD
      MinHighPeriodSeqCount = 0
      MinHighPeriod = RX_END_PERIOD
      for DataRow in ThisRxPacket.Data:
         # Ignore the first and last couple of periods in case they are noise.
         if DataRow[DATA_SEQUENCE] > 2 and DataRow[DATA_SEQUENCE] < DataSize - 2:
            if DataRow[DATA_LEVEL] == 0 and DataRow[DATA_PERIOD] < MinLowPeriod:
               MinLowPeriodSeqCount = DataRow[DATA_SEQUENCE]
               MinLowPeriod = DataRow[DATA_PERIOD]
            if DataRow[DATA_LEVEL] == 1 and DataRow[DATA_PERIOD] < MinHighPeriod:
               MinHighPeriodSeqCount = DataRow[DATA_SEQUENCE]
               MinHighPeriod = DataRow[DATA_PERIOD]
      LogEntry += "MIN LOW PERIOD: [{:d}] {:f} MIN HIGH PERIOD: [{:d}] {:f}\n".format(MinLowPeriodSeqCount, MinLowPeriod, MinHighPeriodSeqCount, MinHighPeriod)

      # Check for data that looks erronious and display an error rather than the data.
      if MinLowPeriod == RX_END_PERIOD or MinHighPeriod == RX_END_PERIOD \
         or MinLowPeriod < RX_REJECT_PERIOD or MinHighPeriod < RX_REJECT_PERIOD:
         BadDataFlag = True
         LogEntry += "! BAD DATA REJECTED !"
      else:
         # Data looks OK, so display the data in several formats to aid decoding of the data.
         # Display binary data and store groups of eight bits as byte data for use later.
         LogEntry += "\nBINARY DATA:\n"
         BitDataCount = 0
         AltBitDataCount = 0
         ByteDataCount = 0
         AltByteDataCount = 0
         ByteData = []
         AltByteData = []
         if RX_BIT_INVERT == 0:
            LevelTest = 0
         else:
            LevelTest = 1
         for DataRow in ThisRxPacket.Data:
            if DataRow[DATA_PERIOD] < RX_END_PERIOD:
               if DataRow[DATA_LEVEL] == LevelTest:
                  # Divide the data level period by the min period for the data level to calculate how many bits are of that level.
                  BitCount = int(round(DataRow[DATA_PERIOD] / MinLowPeriod))
                  for Count in range(BitCount):
                     if ThisRxPacket.StartBitCount > 0:
                        ThisRxPacket.StartBitCount -= 1
                     else:
                        if BitDataCount % 8 == 0:
                           ByteData.append(0)
                           ByteDataCount += 1
                        BitDataCount += 1
                        LogEntry += "0"
                        ByteData[ByteDataCount - 1] = (ByteData[ByteDataCount - 1] << 1) + 0
               else:
                  # Divide the data level period by the min period for the data level to calculate how many bits are of that level.
                  BitCount = int(round(DataRow[DATA_PERIOD] / MinHighPeriod))
                  for Count in range(BitCount):
                     if ThisRxPacket.StartBitCount > 0:
                        ThisRxPacket.StartBitCount -= 1
                     else:
                        if BitDataCount % 8 == 0:
                           ByteData.append(0)
                           ByteDataCount += 1
                        BitDataCount += 1
                        LogEntry += "1"
                        ByteData[ByteDataCount - 1] = (ByteData[ByteDataCount - 1] << 1) + 1

               if BitCount <= 2:
                  if ThisRxPacket.AltStartBitCount > 0:
                     ThisRxPacket.AltStartBitCount -= 1
                  else:
                     if AltBitDataCount % 8 == 0:
                        AltByteData.append(0)
                        AltByteDataCount += 1
                     AltBitDataCount += 1
                     if BitCount == 1:
                        AltByteData[AltByteDataCount - 1] = (AltByteData[AltByteDataCount - 1] << 1) + 0
                     elif BitCount == 2:
                        AltByteData[AltByteDataCount - 1] = (AltByteData[AltByteDataCount - 1] << 1) + 1

         # Display the byte data in hex format.
         LogEntry += "\n\nHEX DATA:\n"
         DataCount = 0
         ZeroTest = 0
         for Byte in ByteData:
            ZeroTest = (ZeroTest | Byte)
            LogEntry += "{:02X} ".format(Byte)
            DataCount += 1
            if DataCount % 26 == 0:
               LogEntry += "\n"
         # Flag all zero data as bad data.
         if ZeroTest == 0:
            BadDataFlag = True

         # Received data decoded from single bit run = 0, double bit run = 1.
         LogEntry += "\n\nALT HEX DATA:\n"
         RxSignatureCount = RX_SIGNATURE_SIZE
         RxSignature = ""
         DataCount = 0
         ZeroTest = 0
         for Byte in AltByteData:
            ZeroTest = (ZeroTest | Byte)
            LogEntry += "{:02X} ".format(Byte)
            if RxSignatureCount > 0:
               RxSignatureCount -= 1
               RxSignature += "{:02X} ".format(Byte)
            DataCount += 1
            if DataCount % 26 == 0:
               LogEntry += "\n"
         LogEntry += "\n\nRX SIGNATURE: {:s}".format(RxSignature)
         # Flag all zero data as bad data.
         if ZeroTest == 0:
            BadDataFlag = True

         # Display the byte data in decimal format.
         LogEntry += "\n\nBYTE DATA:\n"
         DataCount = 0
         for Byte in AltByteData:
            LogEntry += "{:3d} ".format(Byte)
            DataCount += 1
            if DataCount % 19 == 0:
               LogEntry += "\n"

         # Display pairs of the byte data as 16 bit words in decimal format.
         LogEntry += "\n\nWORD DATA OFFSET 0:\n"
         DataWord = 0
         DataCount = 0
         for Byte in AltByteData:
            if DataCount % 2 == 0:
               DataWord = Byte
            else:
               DataWord = (DataWord << 8) + Byte
               LogEntry += "{:6d} ".format(DataWord)

            DataCount += 1
            if DataCount % 20 == 0:
               LogEntry += "\n"

         # Display pairs of the byte data as 16 bit words in decimal format, offset the data by one byte.
         LogEntry += "\n\nWORD DATA OFFSET 1:\n"
         DataWord = 0
         DataCount = 0
         for Byte in AltByteData:
            if DataCount % 2 == 1:
               DataWord = Byte
            else:
               DataWord = (DataWord << 8) + Byte
               LogEntry += "{:6d} ".format(DataWord)

            DataCount += 1
            if DataCount % 20 == 0:
               LogEntry += "\n"

         # Display the byte data in ASCII format.
         LogEntry += "\n\nCHARACTER DATA:\n"
         for Byte in AltByteData:
            LogEntry += "{:s}".format(chr(Byte))

      # Reset data ready to receive next RX data.
      LogEntry += "\n\n\n"

      if BadDataFlag == False or (BadDataFlag == True and LOG_BAD_DATA == True):
         # Open a daily log file.
         LogFile = open("LOG/{:s}_433MHz.log".format(Now.strftime("%Y-%m-%d")), 'a', 0)
         WriteLogLine(LogFile, LogEntry)
         sys.stdout.flush()
         LogFile.close()

      # Initialise a new data packet capture.
      DataInit(ThisRxPacket)

