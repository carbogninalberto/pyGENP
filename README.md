# DISCLAMER
The current library is highly coupled to the project work done for my TCP algorithms optimization thesis. The reason behind this is the strict time required to do both jobs at the same time. Said this, the library is not usable standalone yet. 

`Don't worry, there are good news!`

In the branch `road-to-lib-release` the milestone is to refactor the library to be standalone. A very very brief roadmap is the following:

- version 2: decouple the project
- version 2.1: remove `anytree` and reimplement trees manipulation with `rust`

# Docker image

build docker image from repo
```
docker build --progress=plain --no-cache -t pygenp .
```

run container in local
```
docker run -p 5000:5000 -d pygenp
```

run container using pre-built image
```

```

# PYGENP Genetic Programming library
A (very) essential Genetic Programming library in Python. 

```
The code in this repository is experimental and unstable.
```

## Quick Ref
In order to evolve a set of individuals you need to define custom **operators** or use the one provided by default.
Moreover, you can specify a set of **variable** to use, by **injecting** a initialization value or specify that value is provided by outter **scope**.

The concept of **scope** is important, as long as the root node rappresents the main scope of the evolved program, which could of course contain inner scopes. 

### Registry
There are 2 main registers: **Variables** and **Operators** used in mutation and in random tree generation for the initial population:

- **Variables Registry**: this registry contains all the initialize variables, it enables dynamic variables adding, and variable value mutation in the lifecycle;
- **Operators Registry**: this registry contains all the pre-define operators, it is useful to introduce novelty in the program and complex data manipulation. 

### Parent Selection, Crossover and Mutation
By default **tournament selection** is performed to select the best individuals, that will go to next generation as is and will be also used as genetic parents pool to perform **crossover** and **mutation** for the next generation.  

The following hyperparameters could be customized:

- tournament_size: the number of individual to select for a tournament
- best_individuals: the number of individual to take as-is for the next generation
- replace_individuals: the number of individual to replace (a value between best_individuals < replace_individuals < MAX_POP_SIZE)

#### Crossover
In this phase random part of a individual tree are cutted off and replaced with random ones of a selected parent.

#### Mutation
Different mutations are performed:
- Flib Bit: random number of boolean values are inverted
- Constant Add: a random value is added to constants
- Operator Flip: a operator is flipped with another

### Elitism
The best individual of the current generation has a reserved place in the next one. It doesn't undergo mutation and it can be used as a parent in crossover to generate next generation's offsprings.

### Fitness Calculation
Is possible to provide a custom fitness function and also specify if maximize or minimize it.

### COMPILE

```
CXXFLAGS="-Wno-error" ./waf configure
```

# Docs
```
DISCLAMER! The library is not yet ready for a general usage, still tied to the specific purpose of optimizing a TCP Congestion Protocol over ns3.
```
In this section there is a deeper overview of the library and also of the project.

## Utils
- *clean_memory.sh* is a script to cleanup the pending python threads
- *.env* here you have to specify your ns3 installation folder and the number of CPUS upon running concurrent threads

## NS3 Config & Usage
You need to install ns3 on your local machine, this is the raccomended version: [ns-3.32](https://www.nsnam.org/releases/ns-3-32/).
You need also to edit under `ns-allinone-3.32/ns-3.32/src/internet/model` the file `tcp-congestion-ops.cc` under `IncreaseWindow` function; comment out the code and add the following:

```c++
char * individual = getenv("range");
if (individual != NULL) {
    switch(atoi(individual)) {
//REPLACE

//REPLACE
    default:
        break;
    }
}
```
It is a switch-case that takes as input a terminal variable called `range`; the fitness function will look for the `//REPLACE` comment to add each case that is actually the individual. By doing so you can build ns3 once and run the fitness evaluation in parallel.

You are also required to add a `run.sh` script:

```bash
CXXFLAGS="-Wno-error -Wno-unused-variable" ./waf --run "scratch/wifi-tcp --payloadSize=1500 --simulationTime=1" | tail -10 | grep -P '(?<=: \t)(.*)(?= Mbit\/s)' -o
```

that runs the simulator with `payloadSize=1500`, the default value used over internet providers, and in pipe return just the Throughput as a float value. Notice that to make it executable you need to run:


```bash
sudo chmod +x run.sh
```

You also need to add under `ns-allinone-3.32/ns-3.32/scratch` the file `wifi-tcp` with the following content:

```c++

#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/string.h"
#include "ns3/log.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/ssid.h"
#include "ns3/mobility-helper.h"
#include "ns3/on-off-helper.h"
#include "ns3/yans-wifi-channel.h"
#include "ns3/mobility-model.h"
#include "ns3/packet-sink.h"
#include "ns3/packet-sink-helper.h"
#include "ns3/tcp-westwood.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/ipv4-global-routing-helper.h"

NS_LOG_COMPONENT_DEFINE ("wifi-tcp");

using namespace ns3;

Ptr<PacketSink> sink;                         /* Pointer to the packet sink application */
uint64_t lastTotalRx = 0;                     /* The value of the last total received bytes */

void
CalculateThroughput ()
{
  Time now = Simulator::Now ();                                         /* Return the simulator's virtual time. */
  double cur = (sink->GetTotalRx () - lastTotalRx) * (double) 8 / 1e5;     /* Convert Application RX Packets to MBits. */
  std::cout << now.GetSeconds () << "s: \t" << cur << " Mbit/s" << std::endl;
  lastTotalRx = sink->GetTotalRx ();
  Simulator::Schedule (MilliSeconds (100), &CalculateThroughput);
}

int
main (int argc, char *argv[])
{
  uint32_t payloadSize = 1472;                       /* Transport layer payload size in bytes. */
  std::string dataRate = "100Mbps";                  /* Application layer datarate. */
  std::string tcpVariant = "TcpNewReno";             /* TCP variant type. */
  std::string phyRate = "HtMcs7";                    /* Physical layer bitrate. */
  double simulationTime = 10;                        /* Simulation time in seconds. */
  bool pcapTracing = false;                          /* PCAP Tracing is enabled or not. */

  /* Command line argument parser setup. */
  CommandLine cmd (__FILE__);
  cmd.AddValue ("payloadSize", "Payload size in bytes", payloadSize);
  cmd.AddValue ("dataRate", "Application data ate", dataRate);
  cmd.AddValue ("tcpVariant", "Transport protocol to use: TcpNewReno, "
                "TcpHybla, TcpHighSpeed, TcpHtcp, TcpVegas, TcpScalable, TcpVeno, "
                "TcpBic, TcpYeah, TcpIllinois, TcpWestwood, TcpWestwoodPlus, TcpLedbat ", tcpVariant);
  cmd.AddValue ("phyRate", "Physical layer bitrate", phyRate);
  cmd.AddValue ("simulationTime", "Simulation time in seconds", simulationTime);
  cmd.AddValue ("pcap", "Enable/disable PCAP Tracing", pcapTracing);
  cmd.Parse (argc, argv);

  tcpVariant = std::string ("ns3::") + tcpVariant;
  // Select TCP variant
  if (tcpVariant.compare ("ns3::TcpWestwoodPlus") == 0)
    {
      // TcpWestwoodPlus is not an actual TypeId name; we need TcpWestwood here
      Config::SetDefault ("ns3::TcpL4Protocol::SocketType", TypeIdValue (TcpWestwood::GetTypeId ()));
      // the default protocol type in ns3::TcpWestwood is WESTWOOD
      Config::SetDefault ("ns3::TcpWestwood::ProtocolType", EnumValue (TcpWestwood::WESTWOODPLUS));
    }
  else
    {
      TypeId tcpTid;
      NS_ABORT_MSG_UNLESS (TypeId::LookupByNameFailSafe (tcpVariant, &tcpTid), "TypeId " << tcpVariant << " not found");
      Config::SetDefault ("ns3::TcpL4Protocol::SocketType", TypeIdValue (TypeId::LookupByName (tcpVariant)));
    }

  /* Configure TCP Options */
  Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (payloadSize));

  WifiMacHelper wifiMac;
  WifiHelper wifiHelper;
  wifiHelper.SetStandard (WIFI_STANDARD_80211n_5GHZ);

  /* Set up Legacy Channel */
  YansWifiChannelHelper wifiChannel;
  wifiChannel.SetPropagationDelay ("ns3::ConstantSpeedPropagationDelayModel");
  wifiChannel.AddPropagationLoss ("ns3::FriisPropagationLossModel", "Frequency", DoubleValue (5e9));

  /* Setup Physical Layer */
  YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
  wifiPhy.SetChannel (wifiChannel.Create ());
  wifiPhy.SetErrorRateModel ("ns3::YansErrorRateModel");
  wifiHelper.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                      "DataMode", StringValue (phyRate),
                                      "ControlMode", StringValue ("HtMcs0"));

  NodeContainer networkNodes;
  networkNodes.Create (2);
  Ptr<Node> apWifiNode = networkNodes.Get (0);
  Ptr<Node> staWifiNode = networkNodes.Get (1);

  /* Configure AP */
  Ssid ssid = Ssid ("network");
  wifiMac.SetType ("ns3::ApWifiMac",
                   "Ssid", SsidValue (ssid));

  NetDeviceContainer apDevice;
  apDevice = wifiHelper.Install (wifiPhy, wifiMac, apWifiNode);

  /* Configure STA */
  wifiMac.SetType ("ns3::StaWifiMac",
                   "Ssid", SsidValue (ssid));

  NetDeviceContainer staDevices;
  staDevices = wifiHelper.Install (wifiPhy, wifiMac, staWifiNode);

  /* Mobility model */
  MobilityHelper mobility;
  Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
  positionAlloc->Add (Vector (0.0, 0.0, 0.0));
  positionAlloc->Add (Vector (1.0, 1.0, 0.0));

  mobility.SetPositionAllocator (positionAlloc);
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (apWifiNode);
  mobility.Install (staWifiNode);

  /* Internet stack */
  InternetStackHelper stack;
  stack.Install (networkNodes);

  Ipv4AddressHelper address;
  address.SetBase ("10.0.0.0", "255.255.255.0");
  Ipv4InterfaceContainer apInterface;
  apInterface = address.Assign (apDevice);
  Ipv4InterfaceContainer staInterface;
  staInterface = address.Assign (staDevices);

  /* Populate routing table */
  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

  /* Install TCP Receiver on the access point */
  PacketSinkHelper sinkHelper ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), 9));
  ApplicationContainer sinkApp = sinkHelper.Install (apWifiNode);
  sink = StaticCast<PacketSink> (sinkApp.Get (0));

  /* Install TCP/UDP Transmitter on the station */
  OnOffHelper server ("ns3::TcpSocketFactory", (InetSocketAddress (apInterface.GetAddress (0), 9)));
  server.SetAttribute ("PacketSize", UintegerValue (payloadSize));
  server.SetAttribute ("OnTime", StringValue ("ns3::ConstantRandomVariable[Constant=1]"));
  server.SetAttribute ("OffTime", StringValue ("ns3::ConstantRandomVariable[Constant=0]"));
  server.SetAttribute ("DataRate", DataRateValue (DataRate (dataRate)));
  ApplicationContainer serverApp = server.Install (staWifiNode);

  /* Start Applications */
  sinkApp.Start (Seconds (0.0));
  serverApp.Start (Seconds (1.0));
  Simulator::Schedule (Seconds (1.1), &CalculateThroughput);

  /* Enable Traces */
  if (pcapTracing)
    {
      wifiPhy.SetPcapDataLinkType (WifiPhyHelper::DLT_IEEE802_11_RADIO);
      wifiPhy.EnablePcap ("AccessPoint", apDevice);
      wifiPhy.EnablePcap ("Station", staDevices);
    }

  /* Start Simulation */
  Simulator::Stop (Seconds (simulationTime + 1));
  Simulator::Run ();

  double averageThroughput = ((sink->GetTotalRx () * 8) / (1e6 * simulationTime));

  Simulator::Destroy ();

  if (averageThroughput < 50)
    {
      NS_LOG_ERROR ("Obtained throughput is not in the expected boundaries!");
      exit (1);
    }
  std::cout << "\nAverage throughput: " << averageThroughput << " Mbit/s" << std::endl;
  return 0;
}

```