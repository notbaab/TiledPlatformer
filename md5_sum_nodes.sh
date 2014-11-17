#!/bin/bash
for i in `cat tile-hosts.txt` 
do
    ssh -f $i 'md5sum ~/new_platformer/*'
done