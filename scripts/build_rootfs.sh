#!/bin/bash

SIZE=2048
IMG_NAME=disk.img

TMPDIR=/mnt
PACKAGES="tcpdump quagga bridge-utils radvd vim mingetty"
MIRROR="http://ftp.nl.debian.org/debian"

dd if=/dev/zero of=$IMG_NAME bs=1M count=1 seek=$SIZE
mkfs.ext3 -F $IMG_NAME
mount -o loop $IMG_NAME $TMPDIR
debootstrap --variant=minbase --include="$PACKAGES"  stable $TMPDIR $MIRROR

echo "hostfs /lib/modules hostfs /usr/lib/uml/modules 0 0" >> $TMPDIR/etc/fstab
echo "proc /proc proc defaults 0 0
tmpfs                  /tmp          tmpfs     defaults          0      0
tmpfs                  /var/log          tmpfs     defaults          0      0
tmpfs                  /var/lock          tmpfs     defaults          0      0
tmpfs                  /var/run          tmpfs     defaults          0      0
tmpfs                  /var/tmp          tmpfs     defaults         0      0
" >> $TMPDIR/etc/fstab

for service in quagga radvd cron; do
  chroot $TMPDIR /bin/bash -c "update-rc.d -f $service remove"
done

chroot $TMPDIR /bin/bash -c "mkdir /lib/modules"
mv $TMPDIR/etc/rcS.d/S04hwclockfirst.sh $TMPDIR/etc/rcS.d/K04hwclockfirst
mv $TMPDIR/etc/rcS.d/S06hwclock.sh $TMPDIR/etc/rcS.d/K06hwclock.sh
mv rc.local $TMPDIR/etc/
chmod +x $TMPDIR/etc/rc.local

cp $TMPDIR/etc/inittab $TMPDIR/etc/inittab.save
grep -v "getty" $TMPDIR/etc/inittab.save > $TMPDIR/etc/inittab
echo "1:2345:respawn:/sbin/mingetty --autologin root --noclear tty0" >> $TMPDIR/etc/inittab

echo "tty0" >> $TMPDIR/etc/securetty

echo "auto lo" >> $TMPDIR/etc/network/interfaces
echo "iface lo inet loopback" >> $TMPDIR/etc/network/interfaces

umount $TMPDIR

