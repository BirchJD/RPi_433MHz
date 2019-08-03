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
#/* Pi433MHzRx - 433MHz Receive data.                                        */
#/* ------------------------------------------------------------------------ */
#/* V1.00 - 2019-07-31 - Jason Birch                                         */
#/* ------------------------------------------------------------------------ */
#/* Script for receiving data provided on a 433MHz module.                   */
#/*                                                                          */
#/* Example of the recomended type of data structure to transmit:            */
#/* SIGNITURE [4 bytes] - Unique identifier for each type of data being sent.*/
#/* DATA LEN [1 bytes]  - Total number of bytes being transmitted.           */
#/* DATA [1-255 bytes]  - Encrypted data.                                    */
#/* CHECKSUM [1 byte]   - A checksum of the data sent to verify integrity.   */                                                                        */
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
# Period to signify end of Rx message.
RX_END_PERIOD = 0.01
# Smallest period of high or low signal to consider noise rather than data, and flag as bad data. 
RX_REJECT_PERIOD = 0.000005
# Single level period, one period is a binary 0, two periods are a binary 1. 
RX_LEVEL_PERIOD = 0.000500
# Start bits transmitted to signify start of transmission.
RX_START_BITS = 1
# Minimum received valid packet size.
MIN_RX_BYTES = 4

# Data encryption key.
ENCRYPTION_KEY = [ 0xC5, 0x07, 0x8C, 0xA9, 0xBD, 0x8B, 0x48, 0xEF, 0x88, 0xE1, 0x94, 0xDB, 0x63, 0x77, 0x95, 0x59 ]
# Data packet identifier.
PACKET_SIGNATURE = [ 0x63, 0xF9, 0x5C, 0x1B ]



# A very basic encrypt/decript function, for keeping demonstration code simple. Use a comprehensive function in production code.
def BasicEncryptDecrypt(Data):
   KeyCount = 0
   KeyLen = len(ENCRYPTION_KEY)
   for Count in range(len(Data)):
      Data[Count] ^= ENCRYPTION_KEY[KeyCount]
      if KeyCount >= KeyLen:
         KeyCount = 0



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
# Data packet to transmit.
DataPacket = {
   "SIGNATURE": [],
   "DATA_LENGTH": 0,
   "DATA": [],
   "CHECKSUM": 0,
}

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
         DataCount = 0
         # Validate packet signature.
         MatchFlag = True
         for Count in range(len(PACKET_SIGNATURE)):
            DataPacket["SIGNATURE"].append(ByteData[DataCount])
            if DataPacket["SIGNATURE"][DataCount] != PACKET_SIGNATURE[Count]:
               MatchFlag = False
               break
            DataCount += 1
         if MatchFlag == False:
            sys.stdout.write("INVALID PACKET SIGNATURE\n")
         else:
            DataPacket["DATA_LENGTH"] = ByteData[DataCount]
            DataCount += 1
            for Count in range(DataPacket["DATA_LENGTH"]):
               DataPacket["DATA"].append(ByteData[DataCount])
               DataCount += 1
            DataPacket["CHECKSUM"] = ByteData[DataCount]
            DataCount += 1
            sys.stdout.write("RECEIVED PACKET: " + str(DataPacket) + "\n")
            # Validate packet checksum.
            Checksum = 0
            for Byte in DataPacket["DATA"]:
               Checksum ^= Byte
            if Checksum != DataPacket["CHECKSUM"]:
               sys.stdout.write("INVALID PACKET CHECKSUM\n")
            else:
               # Decrypt and display data.
               BasicEncryptDecrypt(DataPacket["DATA"])
               Data = ""
               for Count in range(DataPacket["DATA_LENGTH"]):
                  Data += chr(DataPacket["DATA"][Count])
               sys.stdout.write("DECRYPTED DATA: {:s}\n".format(Data))
         sys.stdout.write("\n")
         sys.stdout.flush()

      # Reset data to start a new monitor period.
      StartBitFlag = True
      StartBitPeriod = RX_END_PERIOD
      BitCount = 0
      ByteDataCount = 0
      ByteData = []
      # Data packet to transmit.
      DataPacket = {
         "SIGNATURE": [],
         "DATA_LENGTH": 0,
         "DATA": [],
         "CHECKSUM": 0,
      }

