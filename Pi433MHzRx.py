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
#/* DATA LEN [2 bytes]  - Total number of bytes being transmitted.           */
#/* DATA [X bytes]      - Data, encrypted.                                   */
#/* CHECKSUM [2 bytes]  - A checksum of the data sent to verify integrity.   */                                                                        */
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


