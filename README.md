Ogopogo - quickly build virtual network topologies
=========================

Requirements
------------
* Python, user-mode-linux, vde2, screen
* Optionally python-networkx and python-matplotlib

Getting started
---------------
- start network ./ogo.py start config.cfg  - starts the topology
- stop network ./ogo.py stop config.cfg  - stops the topology
- map network ./ogo.py map config.cfg  - this creates a png file of the network topology - useful for debugging setups

Once the network is started you can attach to the console of each device using the 'screen -r <hostname>' command.



Features
--------

Ogo uses UML and vde_switch to create network topologies. Each host is connected to one more more broadcast domains.
A broadcast domain is represented by a uml_switch process. Broadcast domains are numbered starting with 0.

    #  host1 --- (sw0)  ---  host2

In the topology above there is one broadcast domain and two hosts connected to it.




###Creating Devices
Ogo can create three types of network devices:

- switches: VDE switches to which the other devices connect. All VDE switches are started in -hub mode so network sniffers can be attached.
- hosts: UML instances connected to the vde switches. Useful to test pings, services, etc.
- sniffers: they dump via tcpump to $UML_HOME all captured traffic. You can connect to multiple network segments as each segment is dumped to a separate file.
- bridges: using bridge-tools this device bridges two or more ethernet interfaces on the host instances. One instance can support multiple bridges.
- routers: routers load quagga config files via hostfs and start the quagga routing suite. See the examples dir for more detail.

###Slim root file system
The buildroot_fs.sh script creates a slimmed down Debian stable image suitable for user mode linux. Services can be easily
added by adding them to the list of new packages. All the services are removed from startup and are started via rc.local.
Make sure that the owner of the root filesystem disk is the user under which ogo is running. For now, the script creates
a file which is owned by root so you have to manually set permissions.

The root image is expected to be at /tmp/disk.img.

###Drawing
As a debug feature one can draw the network topologies resulted from the config files. This is done via the map argument.

    ./ogo.py map examples/simple.cfg

It's automated so the layout could be better but it still gives a good overview of the network


This has been tested under Ubuntu 12.04 and Debian 6.0.6.


###Contributors
Cosmin Dumitru  - cosu
Jeroen van Der Ham  - jeroenh
Gabor Toth - tg-x : idea to replace uml_switch with vde
