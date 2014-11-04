#!/bin/bash
for i in `cat tile-hosts.txt` 
do
    ssh -f $i 'cd ~/platformer; export DISPLAY=:0.0; sudo python render_node.py'
done