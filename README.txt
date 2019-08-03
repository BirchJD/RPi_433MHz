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



Reading Data Transmitted From A Car Key-fob At 433MHz With A Raspberry Pi


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
received. Allowing analysis and identification of required data transmitted
on 433MHz. Also provides a noise count, which indicates how much local RF
interference (RFI) is being experienced, providing a method of locating the
device in a location with low interference noise, improving reliability of
data reception.

./LogSignatures.sh
Summary of transmitted signatures received and logged with the Pi433MHz.py
application. Along with the number of occurrences, as an aid to identifying
required data being received.

./Pi433MHzRxMatch.py
An example application which identifies specific data being transmitted and
allows an application to be run depending on which of a series of matching
data signatures is identified. Configuration data as a list of data
signatures and commands to execute are placed in the file Pi433MHzRxMatch.ini.

./Pi433MHzTx.py
An example application to take an ASCII string as a command line argument,
which will then be transmitted over 433MHz as part of a data package. The
data package allows the data to be checked for validity on reception in case of
transmission/reception corruption. Demonstrates a basic encryption of the data
on transmission. The Pi433MHz.py application can be used to receive and display
the encrypted data packet. And the Pi433MHzRx.py application can be used to
receive and display the unencrypted data.
e.g.
./Pi433MHzTx.py 'Sending test message.'

./Pi433MHzRx.py
An example application to receive validate, unencrypt and display a packet of
data transmitted from the Pi433MHzTx.py application.



Aerial
======
17cm wound at 5mm diameter spaced to 20mm of 0.5mm enamelled copper wire.
With center ground wire through the coil.


