#!/bin/bash
sudo pkill -f python
sudo pkill -f wifi-tcp
sudo rm -rf snapshots/*
sudo rm -rf snapshots_pickles/*
sudo rm termination_flag