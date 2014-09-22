#!/bin/bash
# run the python programs
python3 render_node.py& > render2.txt
python3 render_node1.py& > render1.txt
sleep 1
python3 game.py 2