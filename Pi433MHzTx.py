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
#/* Pi433MHzTx - 433MHz Transmit specified data.                             */
#/* ------------------------------------------------------------------------ */
#/* V1.00 - 2019-07-31 - Jason Birch                                         */
#/* ------------------------------------------------------------------------ */
#/* Script for transmitting data provided on a 433MHz module.                */
#/*                                                                          */
#/* Example of the recomended type of data structure to transmit:            */
#/* SIGNITURE [4 bytes] - Unique identifier for each type of data being sent.*/
#/* DATA LEN [1 byte]   - Total number of bytes being transmitted.           */
#/* DATA [1-255 bytes]  - Encrypted data.                                    */
#/* CHECKSUM [1 byte]   - A checksum of the data sent to verify integrity.   */                                                                        */
#/****************************************************************************/

import os
import sys
import math
import time
import hashlib
import datetime
import RPi.GPIO



# Number of command line arguments.
ARG_COUNT = 2
# Data to send command line argument.
ARG_EXE = 0
ARG_DATA = 1

# GPIO Pin connected to 433MHz receiver.
GPIO_RX_PIN = 26
# GPIO Pin connected to 433MHz transmitter.
GPIO_TX_PIN = 19

# GPIO level to switch transmitter off.
TX_OFF_LEVEL = 1
# GPIO level to switch transmitter on.
TX_ON_LEVEL = 0
# Period to signify end of Tx message.
TX_END_PERIOD = 0.01
# Single level period, one period is a binary 0, two periods are a binary 1. 
TX_LEVEL_PERIOD = 0.002
# Start bits transmitted to signify start of transmission.
TX_START_BITS = 1

# Data encryption key.
ENCRYPTION_KEY = [ 0xC5, 0x07, 0x8C, 0xA9, 0xBD, 0x8B, 0x48, 0xEF, 0x88, 0xE1, 0x94, 0xDB, 0x63, 0x77, 0x95, 0x59 ]
# Data packet identifier.
PACKET_SIGNATURE = [ 0x63, 0xF9, 0x5C, 0x1B ]



# Data packet to transmit.
DataPacket = {
   "SIGNATURE": PACKET_SIGNATURE,
   "DATA_LENGTH": 0,
   "DATA": [],
   "CHECKSUM": 0,
}



# Transmit a byte of data from the 433MHz module.
def Tx433Byte(Byte):
   global CurrentTxLevel

   BitMask = (1 << 7)
   for BitCount in range(8):
      # Get the next bit from the byte to transmit.
      Bit = (Byte & BitMask)
      BitMask = int(BitMask / 2)

      # Toggle GPIO level.
      if CurrentTxLevel == TX_OFF_LEVEL:
         CurrentTxLevel = TX_ON_LEVEL
      else:
         CurrentTxLevel = TX_OFF_LEVEL
      RPi.GPIO.output(GPIO_TX_PIN, CurrentTxLevel)
      # Bit 0 level period.
      time.sleep(TX_LEVEL_PERIOD)
      # Bit 1 level additional period.
      if Bit > 0:
         time.sleep(TX_LEVEL_PERIOD)



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



# Check for command line argument.
if len(sys.argv) < ARG_COUNT:
   sys.stdout.write("\n" + sys.argv[ARG_EXE] + " [SEND_DATA]\n\n")
else:
   # Place data into data packet and set packet values ready to be sent.
   DataPacket["DATA_LENGTH"] = len(sys.argv[ARG_DATA])
   #Tokenise and encrypt data to be sent.
   DataPacket["DATA"] = list(sys.argv[ARG_DATA])
   for Count in range(len(DataPacket["DATA"])):
      DataPacket["DATA"][Count] = ord(DataPacket["DATA"][Count])
   BasicEncryptDecrypt(DataPacket["DATA"])
   # Calculate checksum of data for transmission validation.
   DataPacket["CHECKSUM"] = 0
   for Byte in DataPacket["DATA"]:
      DataPacket["CHECKSUM"] ^= Byte

   # Display data packet being sent.
   sys.stdout.write("\nSENDING PACKET:\n")
   sys.stdout.write(str(DataPacket) + "\n\n")

   # Switch on 433MHz transmitter.
   CurrentTxLevel = TX_ON_LEVEL
   RPi.GPIO.output(GPIO_TX_PIN, CurrentTxLevel)
   # Wait for the number of start bits.
   for Count in range(TX_START_BITS):
      time.sleep(TX_LEVEL_PERIOD)

   # Transmit data packet signature.
   for Byte in DataPacket["SIGNATURE"]:
      Tx433Byte(Byte)

   # Transmit data packet data length.
   Tx433Byte(DataPacket["DATA_LENGTH"])

   # Transmit data packet encrypted data.
   for Byte in DataPacket["DATA"]:
      Tx433Byte(Byte)

   # Transmit data packet data checksum.
   Tx433Byte(DataPacket["CHECKSUM"])

   # Switch off 433MHz transmitter.
   CurrentTxLevel = TX_OFF_LEVEL
   RPi.GPIO.output(GPIO_TX_PIN, CurrentTxLevel)

   # End of transmission period.
   time.sleep(TX_END_PERIOD)

