#!/bin/bash
for entry in $(find ~/datavault/drives -name '*auto_*.bag')
do
    export xbase=${entry##*/}
    export xpref=${xbase%.*}
    export xext=".xml"
    export xfile=$xpref$xext
    echo $xfile
    ./write_ros_gpx.py --ros-bag $entry --ros-topic /navsat/fix --output-file ~/Data/GPS/$xfile
done