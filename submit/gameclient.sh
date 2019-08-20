#!/bin/bash
cd "$(dirname "$0")"
cd client
pip install numpy
sh start.sh $1 $2 $3
