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



Reading Data Transmitted From A Car Keyfob At 433MHz With A Raspberry Pi


Patreon, donations help produce more OpenSource projects:
https://www.patreon.com/_DevelopIT

Videos of this project:
https://youtu.be/8B582TMMSNY

Source Code on GitHub:
https://github.com/BirchJD/RPi_433MHz



Applications
============

./Pi433MHz.py
Start monitoring and logging data. To provide various views of the data being
received, allowing analysis and identification of required data being 
transmitted on 433MHz. Also provides a noise count, which indicates how much
local RF interferance (RFI) is being experianced, which provides a method of
locating the defice in a location with low interference noise, improving
reception of data.

./LogSignatures.sh
Summary of transmittion signatures and number of occurancies as an aid to 
identifiying the required data being transmitted.

./Pi433MHzRxMatch.py
An example application which identifies specific data being transmitted and
allows an application to be run depending on which of a series of matching
data signatures is identified. Configuration data as a list of data
signatures and commands to execute are placed in the file Pi433MHzRxMatch.ini.

./Pi433MHzTx.py

./Pi433MHzRx.py



Aerial
======
12 Turns spaced to 15mm of 0.315mm enamelled copper wire.


