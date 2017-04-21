#!/bin/bash
apt-get install python-dev
cd "bitarray-0.8.1"
python setup.py install
cd ../pyactor-master
python setup.py install
