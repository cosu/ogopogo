#!/usr/bin/env python

__author__ = 'cdumitru'

import sys, ConfigParser, time, os, logging



def execute(cmd, debug=False):
    logging.info(cmd)
    if not debug: os.system(cmd)


def stop_host( uml_id, config):
    return "uml_mconsole " + uml_id + " halt"


def stop_switch(switch_id, config):
    """ Builds a string to stop an UML switch process

    Arguments:
    switch_id -- the id of the switch to be stopped
    config - global config object

    Returns:
    the stop command as a string
    """

    return "start-stop-daemon --stop --pidfile " + config.get("global", "switch_path") + "/switch"\
           + str(switch_id) + ".pid "


def start_host(uml_id, config, index=0):
    """ Builds the command to start an UML host in a screen session that has the same name as the uml host

    Arguments:
    uml_id -- uml_id to be passed
    config -- global config object
    index -- the index of the device in the list of devices of its type

    Returns:
    the start host command as a string
    """
    cmd = "screen -dmS " + uml_id
    cmd = cmd + " linux.uml umid=" + uml_id + " rootfstype=hostfs "\
                                              "rootflags=" + config.get(uml_id, "rootfs_path") + " name=" + uml_id

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

    cmd = cmd + " interface_count=" + str(interface_count)

    #pass prefix options to uml instance
    for option in config.options(uml_id):
        if option.startswith("pass_"):
            cmd += " " + option[5:] + "=" + config.get(uml_id, option)

    return cmd


def start_switch(id, config):
    """Builds a string to start an uml switch via start-stop-daemon

    Arguments:
    id -- the id of the switch
    config -- global config object

    Returns:
    the start switch command as a string
    """
    #switch ids start at 0!
    switch_id = "switch" + str(id)

    return "start-stop-daemon --start --quiet --background --pidfile "\
          + config.get("global", "switch_path") + "/" + switch_id + \
          ".pid --make-pidfile --exec /usr/bin/uml_switch -- -hub -unix " + \
          config.get("global", "switch_path") + "/" + switch_id + ".ctl"



def start(config, debug=False):
    """Starts a network topology
    Arguments:
    config - global config object
    debug - if true the script only print to stdout

    """
    #start switches
    for i in range(config.getint("global", "switch_count")):
        cmd = start_switch(i, config)
        execute(cmd, debug)

    #start hosts

    devices = {}
    for device in config.sections():
        if device != "global":
            role = config.get(device, "role")

            if  not devices.has_key(role):
                devices[role] = []

            if  role == "sniffer":
                cmd = start_host(device, config)
                execute(cmd, debug)

            else:
                devices[role].append(device)

    #allow sniffers to start
    if not debug: time.sleep(5)
    else: logging.info("#sleep 5")

    #start rest of hosts
    for role  in devices.keys():
        for index, host in enumerate(devices[role]):
            cmd = start_host(host, config, index)
            execute(cmd)




def stop(config, debug=False):
    """Stops a network topology

    Arguments:
    config -- global config object
    debug -- if true the script only print to stdout

    Returns:
    nothing
    """

    #stop hosts
    for device in config.sections():
        if device != "global":
            cmd = stop_host(device, config)
            execute(cmd, debug)
            #stop switches
    for i in range(config.getint("global", "switch_count")):
        cmd = stop_switch(i, config)
        execute(cmd, debug)

def debug(config):
    """Executes start and stop in debug mode

    Arguments:
    config -- global config object
    Returns:
    nothing
    """
    start(config, True)
    stop(config, True)


def draw(config):
    """
    Draws a png file of the network topology and places it in the current directory.
    The file name is the same as with the config file but with the extension .png

    Arguments:
    config -- global config object
    Returns:
    nothing
    """
    pass


def main():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

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



