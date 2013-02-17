#!/bin/bash

#author: Cosmin 'cosu' Dumitru <c.dumitru@uva.nl>

#This script builds a ready to run User mode linux image. A file called rc.local should be present next to this script to
# enable extra functionality. This script must be run as root. If you decide to run the UML machine as a regular user
# make sure you change the permisions of the image as the resulting image file will be owned by root

#========Config
#image size. note that the image is created as a sparse file
SIZE=2048
#image name
IMG_NAME=disk.img
#list of extra packages to be installed
SERVICES="quagga radvd bird"
PACKAGES="tcpdump bridge-utils"
BASE_PACKAGES="iproute net-tools iputils-ping traceroute mingetty module-init-tools procps vim"
#to speedup installation use a nearby mirror
MIRROR="http://ftp.nl.debian.org/debian"
#=======Config ends here


#tmpdir used to mount the image for debootstrap
TMPDIR=/mnt


#check for root
if [ `whoami` != root ]; then
    echo Please run this script as root or using sudo
    exit
fi


#build image file
dd if=/dev/zero of=$IMG_NAME bs=1M count=1 seek=$SIZE
mkfs.ext3 -F $IMG_NAME
mount -o loop $IMG_NAME $TMPDIR


#install base system
debootstrap --variant=minbase --include="$PACKAGES $BASE_PACKAGES $SERVICES "  stable $TMPDIR $MIRROR

#configure uml modules via hostfs
echo "hostfs /lib/modules hostfs /usr/lib/uml/modules 0 0" >> $TMPDIR/etc/fstab
echo "proc /proc proc defaults 0 0
tmpfs                  /tmp          tmpfs     defaults          0      0
tmpfs                  /var/log          tmpfs     defaults          0      0
tmpfs                  /var/lock          tmpfs     defaults          0      0
tmpfs                  /var/run          tmpfs     defaults          0      0
tmpfs                  /var/tmp          tmpfs     defaults         0      0
" >> $TMPDIR/etc/fstab

#disable services at startup. we'll start them in a role based fashion later
for service in $SERVICES; do
  chroot $TMPDIR /bin/bash -c "update-rc.d -f $service remove" 2>/dev/null
done

#remove some services to speedup startup
mv $TMPDIR/etc/rcS.d/S06module-init-tools $TMPDIR/etc/rcS.d/K08module-init-tools

#copy our own version of rc.local to enable roles
cp rc.local $TMPDIR/etc/
chmod +x $TMPDIR/etc/rc.local

#backup inittab
cp $TMPDIR/etc/inittab $TMPDIR/etc/inittab.save
#modify inittab for root autologin
grep -v "getty" $TMPDIR/etc/inittab.save > $TMPDIR/etc/inittab
echo "1:2345:respawn:/sbin/mingetty --autologin root --noclear tty0" >> $TMPDIR/etc/inittab

#allow connections from the local console
echo "tty0" >> $TMPDIR/etc/securetty

#basic network config
echo "auto lo" >> $TMPDIR/etc/network/interfaces
echo "iface lo inet loopback" >> $TMPDIR/etc/network/interfaces


umount $TMPDIR

chown ${SUDO_USER}: $IMG_NAME
