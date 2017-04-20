#!/bin/bash
pid=$(lsof -i:6970 -t)
pid2=$(lsof -i:6969 -t)
echo "Open ports"
echo "$pid $pid2"
kill -9 $pid $pid2
pid=$(lsof -i:6970 -t)
pid2=$(lsof -i:6969 -t)
echo "After kill"
echo "$pid $pid2"
