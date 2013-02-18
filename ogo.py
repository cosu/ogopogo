#!/usr/bin/env python

__author__ = 'cdumitru'

import sys
import ConfigParser
import time
import os
import logging

_debug = False


def execute(cmd):
    global _debug
    logging.debug(cmd)
    if not _debug:
        os.system(cmd)


def stop_host(uml_id, config):
    cow_path = config.get("global", "session_path")
    root_image = config.get("global", "root_image")
    root_file = root_image.split("/")[-1]
    remove_cow_cmd = "rm -f {cow_path}/{root_file}-{uml_id}.cow".format(**locals())
    halt_uml_cmd = "uml_mconsole {uml_id} halt".format(**locals())


    execute(remove_cow_cmd)
    execute(halt_uml_cmd)


def stop_switch(switch_id, config):
    """ Builds a string to stop an UML switch process

    Arguments:
    switch_id -- the id of the switch to be stopped
    config - global config object

    Returns:
    nothing
    """

    switch_path = config.get("global", "session_path")

    cmd = "start-stop-daemon --stop --pidfile {switch_path}/switch-{switch_id}.pid".format(**locals())

    execute(cmd)


def start_host(uml_id, config, index=0):
    """ Builds the command to start an UML host in a screen session that has the same name as the uml host

    Arguments:
    uml_id -- uml_id to be passed
    config -- global config object
    index -- the index of the device in the list of devices of its type

    Returns:
    nothing
    """
    cmd = []
    #normalize index
    # the index must be 2 digits
    idx = str(hex(index))[2:]
    if len(idx) < 2:
        idx = "0" + idx

    role = config.get(uml_id, "role")
    cow_path = config.get("global", "session_path")
    root_image = config.get("global", "root_image")
    root_image_name = root_image.split("/")[-1]

    cow_file = "{cow_path}/{root_image_name}-{uml_id}.cow".format(**locals())

    screen_cmd = "screen -dmS {uml_id} linux.uml umid={uml_id} role={role} index={idx} name={uml_id} " \
                 "ubd0={cow_file},{root_image}".format(**locals())
    cmd .append(screen_cmd)

    mk_cow_cmd = "uml_mkcow -f {cow_file} {root_image}".format(**locals())
    execute(mk_cow_cmd)

    #count interfaces
    interface_count = 0
    for interface in config.options(uml_id):

        if interface.startswith("eth"):
            interface_idx = interface.lstrip("eth")
            network_info = config.get(uml_id, interface).split(',')
            ipv4 = False
            ipv6 = False
            to_switch = ""

            if len(network_info) == 3:
                (to_switch, ipv4, ipv6) = network_info
            elif len(network_info) == 2:
                (to_switch, ipv4) = network_info
            else:
                to_switch = network_info

            #check for tuntap
            if to_switch.startswith("tap"):
                eth = "{interface}=tuntap,".format(**locals())
                sw = "{to_switch},,".format(**locals())
            else:
                eth = "{interface}=daemon,,unix,".format(**locals())
                switch_path = config.get("global", "session_path")
                sw = "{switch_path}/switch-{to_switch}.ctl".format(**locals())

            cmd.append(eth + sw)

            if ipv4:
                iface = "ip{interface_idx}={ipv4}".format(**locals())
                cmd.append(iface)
            if ipv6:
                iface = "ip6{interface_idx}={ipv6}".format(**locals())
                cmd.append(iface)

            interface_count += 1

    #custom mem setting per host
    mem = config.get("global", "mem")
    if config.has_option(uml_id, "mem"):
        mem = config.get(uml_id, "mem")

    mem = "mem={mem} interface_count={interface_count}".format(**locals())
    cmd.append(mem)

    if config.has_option(uml_id, "home"):
        home = "home=" + config.get(uml_id, "home")
        cmd.append(home)

    #pass prefix options to uml instance
    for option in config.options(uml_id):
        if option.startswith("pass_"):
            passopt = option[5:] + "=" + config.get(uml_id, option)
            cmd.append(passopt)

    cmd = " ".join(cmd)

    execute(cmd)


def start_switch(id, config):
    """Builds a string to start an uml switch via start-stop-daemon

    Arguments:
    id -- the id of the switch
    config -- global config object

    Returns:
    nothing
    """
    #switch ids start at 0!
    switch_id = "switch-{0}".format(id)
    switch_path = config.get("global", "session_path")

    cmd = "start-stop-daemon --start --quiet --background --pidfile {switch_path}/{switch_id}.pid " \
          "--make-pidfile --exec /usr/bin/uml_switch -- -hub -unix {switch_path}/{switch_id}.ctl".format(**locals())
    execute(cmd)


def start(config):
    """Starts a network topology
    Arguments:
    config - global config object

    """
    #start switches
    for i in range(config.getint("global", "broadcast_domains")):
        start_switch(i, config)

    #start hosts

    devices = {}
    sniffer = False
    for device in config.sections():

        if device != "global":

            role = config.get(device, "role")
            if not role in devices.keys():
                devices[role] = []

            if role == "sniffer":
                sniffer = True
                logging.info("Starting sniffer {0}".format(device))
                start_host(device, config)

            else:
                devices[role].append(device)

    #allow sniffers to start
    if sniffer:
        global _debug
        if not _debug:
            logging.info("sleeping 5 seconds to allow sniffers to start first")
            time.sleep(5)

    #start rest of hosts
    for role in devices.keys():
        for index, host in enumerate(devices[role]):
            logging.info("Starting host {0}".format(host))
            time.sleep(0.5)
            start_host(host, config, index)

    execute("screen -ls")


def stop(config):
    """Stops a network topology

    Arguments:
    config -- global config object

    Returns:
    nothing
    """

    #stop hosts
    for device in config.sections():
        if device != "global":
            logging.info("Stopping device {0}".format(device))
            stop_host(device, config)
            #stop switches
    for i in range(config.getint("global", "broadcast_domains")):
        logging.info("Stopping switch {0}".format(i))
        stop_switch(i, config)


def debug(config):
    """Executes start and stop in debug mode

    Arguments:
    config -- global config object
    Returns:
    nothing
    """
    global _debug
    _debug = True
    start(config)
    stop(config)


def draw(config):
    """
    Draws a png file of the network topology and places it in the current directory.
    The file name is the same as with the config file but with the extension .png

    Arguments:
    config -- global config object
    Returns:
    nothing
    """

    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.Graph()

    for device in config.sections():
        if device != "global":
            for interface in config.options(device):
                if interface.startswith("eth"):
                    to_switch = int(config.get(device, interface).split(',')[0])
                    print "adding: " + "switch" + str(to_switch) + "->" + device
                    G.add_edge(to_switch, device)

    pos = nx.spring_layout(G)

    hosts = config.sections()
    sniffers = []
    hosts.remove("global")
    for host in hosts:
        if config.get(host, "role") == "sniffer":
            sniffers.append(host)
            hosts.remove(host)

    switches = range(config.getint("global", "broadcast_domains"))

    nx.draw_networkx_nodes(G, pos, nodelist=hosts, node_color='red', alpha=0.6, node_size=400)
    nx.draw_networkx_nodes(G, pos, nodelist=switches, node_color='green', alpha=0.6, node_size=400)
    nx.draw_networkx_nodes(G, pos, nodelist=sniffers, node_color='blue', alpha=0.6, node_size=250)

    nx.draw_networkx_edges(G, pos, alpha=0.5, width=3)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.axis('off')
    plt.savefig(sys.argv[2] + ".png")


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    if len(sys.argv) != 3:
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0] + \
              "<start|stop|map> <config file>"
        sys.exit(0)

    if ((sys.argv[1] != "start") and (sys.argv[1] != "stop") and (sys.argv[1] != "map") and (
            sys.argv[1] != "status") and (sys.argv[1] != "debug")):
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0] + \
              "<start|stop|status|map> <config file>"
        sys.exit(0)

    try:
        config = ConfigParser.ConfigParser()
        configFile = sys.argv[2]
        config.read(configFile)
    except:
        print "Error reading config file " + sys.argv[2]
        sys.exit(0)

    action = sys.argv[1]

    if action == "start":
        start(config)
    elif action == "stop":
        stop(config)
    elif action == "map":
        draw(config)
    elif action == "debug":
        debug(config)


if __name__ == "__main__":
    main()
