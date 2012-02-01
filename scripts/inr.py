#!/usr/bin/env python

__author__ = 'cdumitru'

import sys, ConfigParser, time, os, logging

_debug=False

def execute(cmd):
    global _debug
    logging.info(cmd)
    if not _debug: os.system(cmd)


def stop_host( uml_id, config):
    cow_path = config.get("global", "cow_path")
    root_image = config.get("global", "root_image")
    cow_file = cow_path +"/"+ root_image.split("/")[-1] +"-"+uml_id+".cow"
    execute("rm -f " + cow_file)
    execute("uml_mconsole " + uml_id + " halt")



def stop_switch(switch_id, config):
    """ Builds a string to stop an UML switch process

    Arguments:
    switch_id -- the id of the switch to be stopped
    config - global config object

    Returns:
    nothing
    """

    execute( "start-stop-daemon --stop --pidfile " + config.get("global", "switch_path") + "/switch"\
           + str(switch_id) + ".pid ")


def start_host(uml_id, config, index=0):
    """ Builds the command to start an UML host in a screen session that has the same name as the uml host

    Arguments:
    uml_id -- uml_id to be passed
    config -- global config object
    index -- the index of the device in the list of devices of its type

    Returns:
    nothing
    """
    cmd = "screen -dmS -L " + uml_id
    #normalize index
    # the index must be 2 digits
    idx = str(hex(index))[2:]
    if len(idx) < 2:
        idx = "0" +idx

    cmd += " linux.uml umid=" + uml_id + " role=" + config.get(uml_id,"role") + " index=" + idx + " name=" + uml_id


    cow_path = config.get("global", "cow_path")
    root_image = config.get("global", "root_image")
    cow_file = cow_path +"/"+ root_image.split("/")[-1] +"-"+uml_id+".cow"

    execute("uml_mkcow -f " + cow_file + " " + root_image)

    cmd += " ubd0=" + cow_file + ","+root_image


    #count interfaces
    interface_count = 0

    for interface in config.options(uml_id):
        if interface.startswith("eth"):
            (to_switch, ip) = config.get(uml_id, interface).split(',')
            eth = " " + interface + "=daemon,,unix,"
            sw = config.get("global", "switch_path") + "/switch" + to_switch + ".ctl"
            cmd = cmd + eth + sw

            if ip:
                iface = " ip" + str(interface_count) + "=" + ip + " "
                cmd += iface
            interface_count+=1

    cmd +=  " interface_count=" + str(interface_count) + " ubd=mmap mem=" + config.get("global", "mem")


    #pass prefix options to uml instance
    for option in config.options(uml_id):
        if option.startswith("pass_"):
            cmd += " " + option[5:] + "=" + config.get(uml_id, option)

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
    switch_id = "switch" + str(id)

    cmd =  "start-stop-daemon --start --quiet --background --pidfile "\
          + config.get("global", "switch_path") + "/" + switch_id + \
          ".pid --make-pidfile --exec /usr/bin/uml_switch -- -hub -unix " + \
          config.get("global", "switch_path") + "/" + switch_id + ".ctl"
    execute(cmd)


def start(config):
    """Starts a network topology
    Arguments:
    config - global config object

    """
    #start switches
    for i in range(config.getint("global", "switch_count")):
        start_switch(i, config)

    #start hosts

    devices = {}
    for device in config.sections():
        if device != "global":
            role = config.get(device, "role")

            if  not devices.has_key(role):
                devices[role] = []

            if  role == "sniffer":
                start_host(device, config)


            else:
                devices[role].append(device)

    #allow sniffers to start
    global _debug
    if not _debug: time.sleep(5)
    else: logging.info("#sleep 5")

    #start rest of hosts
    for role  in devices.keys():
        for index, host in enumerate(devices[role]):
            start_host(host, config, index)





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
            stop_host(device, config)
            #stop switches
    for i in range(config.getint("global", "switch_count")):
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

            for i in range( 4 ):
                if hosts[h].has_key( "connect" + str( i ) ):
                    print "adding: " + "switch" + str( i ) + "->" + hosts[h]["name"]
                    G.add_edge( hosts[h]["connect" + str( i )], hosts[h]["name"] )

    pos = nx.spring_layout( G )

    nx.draw_networkx_nodes( G, pos, nodelist=switches.keys(), node_color='red', alpha=0.6, node_size=400 )
    nx.draw_networkx_nodes( G, pos, nodelist=hosts.keys(), node_color='green', alpha=0.6, node_size=400 )
    nx.draw_networkx_edges( G, pos, alpha=0.5, width=3 )
    nx.draw_networkx_labels( G, pos, font_size=8 )
    plt.axis( 'off' )
    plt.savefig( sys.argv[2] + ".png" )

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    if  len(sys.argv) != 3:
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0] +\
              "<start|stop|status|map> <config file>"
        sys.exit(0)

    if (( sys.argv[1] != "start" ) and ( sys.argv[1] != "stop" ) and ( sys.argv[1] != "map" ) and (
        sys.argv[1] != "status" ) and (sys.argv[1] != "debug")):
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0] +\
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



