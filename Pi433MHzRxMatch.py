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
#/* Pi433MHzRx - 433MHz Received data recognition and reaction.              */
#/* ------------------------------------------------------------------------ */
#/* V1.00 - 2019-07-31 - Jason Birch                                         */
#/* ------------------------------------------------------------------------ */
#/* Script for monitoring a 433MHz and running scripts for recognised data   */
#/* types. This script assumes data encoding of short level = binary 0,      */
#/* long level = binary 1.                                                   */
#/****************************************************************************/



import os
import sys
import math
import time
import datetime
import RPi.GPIO



# GPIO Pin connected to 433MHz receiver.
GPIO_RX_PIN = 26
# GPIO Pin connected to 433MHz transmitter.
GPIO_TX_PIN = 19

# GPIO level to switch transmitter off.
TX_OFF_LEVEL = 1
# Period of no RX data to consider end of RX data message.
RX_END_PERIOD = 0.01
# Smallest period of high or low signal to consider noise rather than data, and flag as bad data. 
RX_REJECT_PERIOD = 0.000005
# Minimum number of bytes of data received to be considered valid.
MIN_RX_BYTES = 4
# Log received data which does not match.
LOG_NO_MATCH = False

# Config data fields:
CONFIG_ELEMENT_MATCH = 0
CONFIG_ELEMENT_COMMAND = 1



# Read a configuration data file.
def LoadConfig():
   ConfigData = []
   File = open("Pi433MHzRxMatch.ini", 'r', 0)
   TextLine = "."
   while TextLine != "":
      TextLine = File.readline().replace("\n", "")
      if TextLine != "":
         Element = TextLine.split("=")
         ConfigData.append(Element)
   File.close()
   
   return ConfigData



#  /*******************************************/
# /* Configure Raspberry Pi GPIO interfaces. */
#/*******************************************/
RPi.GPIO.setwarnings(False)
RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(GPIO_RX_PIN, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
RPi.GPIO.setup(GPIO_TX_PIN, RPi.GPIO.OUT, initial=TX_OFF_LEVEL)


# Initialise data.
StartBitFlag = True
ThisPeriod = RX_END_PERIOD
StartBitPeriod = RX_END_PERIOD
LastBitPeriod = RX_END_PERIOD
LastGpioLevel = 1
BitCount = 0
ByteDataCount = 0
ByteData = []

# Read configuration data.
ConfigData = LoadConfig()

# Infinate loop for this application.
sys.stdout.write("\nWAITING FOR DATA...\n\n")
sys.stdout.flush()
ExitFlag = False
while ExitFlag == False:
   # Check if data is currently being received.
   ThisPeriod = time.time()
   DiffPeriod = ThisPeriod - LastBitPeriod

   # If data level changes, decode long period = 1, short period = 0.
   GpioLevel = RPi.GPIO.input(GPIO_RX_PIN)
   if GpioLevel != LastGpioLevel:
      # Ignore noise.
      if DiffPeriod > RX_REJECT_PERIOD:
         # Wait for start of communication.
         if StartBitFlag == True:
            # Calculate start bit period, consider as period for all following bits.
            if StartBitPeriod == RX_END_PERIOD:
               StartBitPeriod = ThisPeriod
            else:
               StartBitPeriod = (ThisPeriod - StartBitPeriod) * 0.90
               StartBitFlag = False
         else:
            if DiffPeriod < StartBitPeriod:
               StartBitPeriod = DiffPeriod

            # Receiving a data level, convert into a data bit.
            Bits = int(round(DiffPeriod / StartBitPeriod))
            if BitCount % 8 == 0:
               ByteData.append(0)
               ByteDataCount += 1
            BitCount += 1
            ByteData[ByteDataCount - 1] = (ByteData[ByteDataCount - 1] << 1)
            if Bits > 1:
                ByteData[ByteDataCount - 1] |= 1
         LastBitPeriod = ThisPeriod
      LastGpioLevel = GpioLevel
   elif DiffPeriod > RX_END_PERIOD:
      # End of data reception.
      if ByteDataCount >= MIN_RX_BYTES and StartBitPeriod > RX_REJECT_PERIOD:
         # Format the byte data in hex format.
         DataString = ""
         DataCount = 0
         for Byte in ByteData:
            DataString += "{:02X}".format(Byte)
            DataCount += 1

         # Check for data match, checking from the start of data for the number of bytes in the config data, ignoring the remainder of received data.
         Match = False
         for ConfigElement in ConfigData:
            ConfigMatchLen = len(ConfigElement[CONFIG_ELEMENT_MATCH])
            if ByteDataCount * 2 >= ConfigMatchLen and DataString[:ConfigMatchLen] == ConfigElement[CONFIG_ELEMENT_MATCH]:
               Match = True
               break

         # Respond to a data match.
         if Match == True:
            Now = datetime.datetime.now()
            sys.stdout.write(Now.strftime("%Y-%m-%d %H:%M:%S\n"))
            sys.stdout.write("MATCH: " + str(ConfigElement) + "\n")
            sys.stdout.write("START BIT PERIOD {:f}\n".format(StartBitPeriod))
            sys.stdout.write(DataString + "\n")
            sys.stdout.flush()
            os.system(ConfigElement[CONFIG_ELEMENT_COMMAND])
            sys.stdout.write("\n\n")
            sys.stdout.flush()
         elif LOG_NO_MATCH == True:
            Now = datetime.datetime.now()
            sys.stdout.write(Now.strftime("%Y-%m-%d %H:%M:%S\n"))
            sys.stdout.write("NO MATCH: " + str(ConfigElement) + "\n")
            sys.stdout.write("START BIT PERIOD {:f}\n".format(StartBitPeriod))
            sys.stdout.write(DataString + "\n")
            sys.stdout.flush()

      # Reset data to start a new monitor period.
      StartBitFlag = True
      StartBitPeriod = RX_END_PERIOD
      BitCount = 0
      ByteDataCount = 0
      ByteData = []

