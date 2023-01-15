# crashwatch
Crashwatch is a python script that monitors a file (e.g. Linux kernel log) for an error message or any phrase, and runs a command whenever that phrase is found.

This was created when I had a weird bug with my laptop, where driver for the internal PS/2 keyboard and trackpad bugged out periodically. Whenever this happened, an error was logged into the kernel log "/var/log/kern.log", so I made a script that monitors that log file and automatically uses modprobe to restart the PS/2 drivers when this happens.
