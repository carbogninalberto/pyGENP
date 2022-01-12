git clone https://github.com/carbogninalberto/pyGENP.git
apt-get update
apt install python3-pip -y
apt install unzip -y
apt install zip -y
pip install gdown
# ready ns3 configuration
#gdown https://drive.google.com/u/1/uc?id=1fXZM_KcW6sxfGTa1mEPPZ4yohFNRb8Om
gdown https://drive.google.com/u/1/uc?id=1wcOhk2sjE2hrjjX0P4LwtMObxldg-Cvb
#unzip sim.zip -d /root/ns3
unzip sim2.zip -d /root/ns3
mv ns3/mnt/c/Users/carbo/Desktop/Unitn/tesi/* ns3
cd ns3
rm -rf mnt
cd ~
# you may want to change the number of CPUS regarding your hardware
echo -e "BASE_NS3_PATH=\"/root/ns3/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32\"\nCPUS=8" > pyGENP/.env
cd /root/ns3/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32/
./waf configure
cd ~
echo "cd ~
cd pyGENP
source venv/bin/activate
python server.py" >> run.sh
chmod +x run.sh
cd pyGENP
apt install python3.8-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ufw allow 5000
python server.py