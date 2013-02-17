Ogopogo - quickly build virtual network topologies.
=========================

Requirements
------------
Python, user-mode-linux, screen
Optionally python-networkx and python-matplotlib

Getting started
---------------
- write a cfg file using .ini/properties format (see /examples)
- start network ./ogo.py start config.cfg  - starts the topology
- stop network ./ogo.py stop config.cfg  - stops the topology
- map network ./ogo.py map config.cfg  - this creates a png file of the network topology - useful for debugging setups

Once the network is started you can attach to the console of each device using the screen utility:

    root@uml-host:~# screen -ls
    There are screens on:
        24026.host7	(02/16/12 10:43:58)	(Detached)
        24127.host8	(02/16/12 10:43:58)	(Detached)
        24102.host1	(02/16/12 10:43:58)	(Detached)
        24049.host5	(02/16/12 10:43:58)	(Detached)
        24113.host9	(02/16/12 10:43:58)	(Detached)
        24075.host3	(02/16/12 10:43:58)	(Detached)
        24089.host2	(02/16/12 10:43:58)	(Detached)
        24063.host4	(02/16/12 10:43:58)	(Detached)
        24036.host6	(02/16/12 10:43:58)	(Detached)
        23664.sniffer1	(02/16/12 10:43:53)	(Detached)

Connect to host1

    root@uml-host:~# screen -r host1


Features
--------

###Creating Devices
The script can create three types of network devices:

- switches: UML switches to which the other devices connect. All switches are started in -hub mode so network sniffers can be attached.
- hosts: UML instances connected to the switches. Useful to test pings, services, etc.
- sniffers: they dump via tcpump to $UML_HOME all captured traffic. You can connect to multiple network segments as each segment is dumped to a separate file.
- bridges: using bridge-tools this device bridges two or more ethernet interfaces. One instance supports multiple bridges
- routers:  routers load quagga config files via hostfs and start the quagga routing suite. See the examples dir for more detail

###Drawing
As a debug feature one can draw the network topologies resulted from the config files. This is done via the map argument.

    ./ogo.py map simple.cfg

It's automated so the layout could be better but it still gives a good overview of the network


