# -* bash *-
### BEGIN INIT INFO
# Provides: rctstart
# Required-Start: $portmap $time $remote_fs
# Required-Stop:
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Start radio collar tracker payload on switch
### END INIT INFO
# setup here
timestamp() {
	date
}

PATH=/sbin:/usr/sbin:/bin:/usr/bin:/usr/local/bin

INSTALL_DIR=&INSTALL_PREFIX

case "$1" in
	stop)
		killall rctrun &
		echo "Service stopped!"
		rm -f /var/lock/rctstart
		exit
		;;
	start)
		# start
		if [ ! -f /var/lock/rctstart ]; then
			$INSTALL_DIR/bin/rctrun &
			echo "Service started!"
			touch /var/lock/rctstart
		fi
		exit
		;;
	restart|reload|condrestart)
		killall rctrun &
		echo "Service started!"
		$INSTALL_DIR/bin/rctrun &
		exit
		;;
esac
