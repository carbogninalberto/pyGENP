import psutil

PROCWIFITCP = "wifi-tcp"

for proc in psutil.process_iter():
    # check whether the process name matches
    if proc.name() == PROCWIFITCP:
        proc.kill()