# DEPLOY

Deploying multiple servers at once is essential. The project complexity reached a point where manual configuration is tedius. I wrote some useful scripts to automate some processes. Still not fully automated, but it's a good starting point.

### ENVIRONMENT CONFIGURATION
You may want to setup the (virtual) machines to configure and gather their IP addresses.
After doing that you may want to modify the `/etc/hosts` file to map the ip to a custom domain name in the shape of `runner-xx` (eg. `runner-1`). 

In Windows with WSL 1 you need to modify the file in the path `C:\Windows\System32\drivers\etc\hosts` to make it persistent across sessions, (you need to reopen a new session).

### CONFIGURATION SCRIPT
So far, so good, the `config.sh` is a script to run if you want to configure the environment to run the application.

### RUNNERS SCRIPT
The reported scripts are assuming 6 machines, they need to be customized:
- `multiple_config.sh` -> running this script you automatically configure all the runners
- `reboot.sh` -> reboot all the runners
- `run_tunnel.sh` -> run the application server and create a ssh tunnel of remote port 5000 to the local port 50xx where xx is the runner number
- `tunnel.sh` -> ssh tunnel to port 50xx

### MERGING_SCRIPTS
In the folder `merging_scripts` there are a couple of scripts to help merging different snapshots. For instance you ran 20 generations and want to continue until 50. In the application you save the first snapshot at 20 generations, you reimport it and set 30 generations. Once finished you export another snapshot and to merge them you may want to use them instead of manually change folders name.
