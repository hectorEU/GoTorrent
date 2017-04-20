#!/bin/bash
pid=$(lsof -i:6969 -t)
echo "Open ports"
echo "$pid"
kill -9 $pid
pid=$(lsof -i:6969 -t)
echo "After kill"
echo "$pid"
