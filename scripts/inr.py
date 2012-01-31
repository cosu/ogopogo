__author__ = 'cdumitru'


__author__ = 'cdumitru'


import sys, ConfigParser, time, os


def stop_host( host_id, config):
    cmd = "uml_mconsole " + host_id + " halt"
    if ( config.get("global","debug") == "true" ):
        os.system( 'echo ' + cmd )
    else:
        os.system( cmd )

def stop_switch(switch_id, config):
    cmd = "start-stop-daemon --stop --pidfile " + config.get("global","switch_path") + "/"\
             + str(switch_id) + ".pid "

    if ( config.get("global","debug") == "true" ):
        os.system( 'echo ' + cmd )
    else:
        os.system( cmd )



def start_host(host_id,config):

    ##main cmd
    cmd = "screen -dmS " + host_id
    cmd = cmd + " linux.uml umid=" + host_id + " rootfstype=hostfs "\
        "rootflags=" + config.get(host_id, "rootfs_path") + " name=" + host_id

    ##interfaces

    interface_count = config.getint(host_id, "interface_count")

    cmd = cmd + " interface_count="+str(interface_count)

    for i in range(interface_count):
        (to_switch, ip) = config.get(host_id,"eth"+str(i)).split(',')
        eth = " eth" + str( i ) + "=daemon,,unix,"
        sw = config.get("global", "switch_path") +"/switch"+to_switch+".ctl"
        cmd = cmd + eth + sw
        if (ip ):
            iface = " ip" + str( i ) + "=" + ip +" "
            cmd = cmd + iface

    #pass prefix options to uml instance
    for option in config.options(host_id):
        if option.startswith("pass_"):
            cmd += " " +option[5:]+ "=" + config.get(host_id, option)



    if  config.get("global","debug") == "true" :
        os.system( 'echo ' + cmd )
    else:
        os.system( cmd )


def start_switch(id, config):

    switch_id = "switch"+str(id)

    cmd = "start-stop-daemon --start --quiet --background --pidfile " \
    + config.get("global", "switch_path") + "/" + switch_id + ".pid --make-pidfile --exec"\
    " /usr/bin/uml_switch -- -hub -unix " + config.get("global", "switch_path") + "/" \
    + switch_id+ ".ctl"

    #exec
    if ( config.get("global","debug") == "true" ):
        os.system( 'echo ' + cmd )
    else:
        os.system( cmd )
	os.system( 'echo ' + cmd )


def main():

    if  len( sys.argv ) != 3 :
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0]+\
        "<start|stop|status|map> <config file>"
        sys.exit( 0 )

    if ( ( sys.argv [1] != "start" ) and ( sys.argv [1] != "stop" ) and ( sys.argv[1] != "map" ) and ( sys.argv[1] != "status" ) ):
        print "ERROR: Invalid arguments. Usage : " + sys.argv[0]+\
        "<start|stop|status|map> <config file>"
        sys.exit( 0 )

    try:
        config = ConfigParser.ConfigParser()
        configFile = sys.argv[2]
        config.read( configFile )
    except :
        print "Error reading config file " + sys.argv[2]
        sys.exit( 0 )

    action = sys.argv[1]


    if action == "start" :
        #start switches
        for i in range(config.getint("global", "switch_count")):
            start_switch(i, config)
        #start hosts
        for device in config.sections():
            if (device!="global"):
                hosts=[]
                if (config.get(device, "role") == "sniffer"):
                    start_host(device, config)
                else:
                    hosts.append(device)

                #allow sniffers to start
                #time.sleep(5)

                #start rest of hosts
                for host in hosts:
                    start_host(host, config)


    elif action == "stop":
        #stop hosts
        for device in config.sections():
                    if (device!="global"):
                        stop_host(device, config)
        #stop switches
        for i in range(config.getint("global", "switch_count")):
                    stop_switch(i, config)




if __name__ == "__main__":
    main()



