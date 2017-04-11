#!/bin/bash
kill -9 $(lsof -i:6666 -t)
kill -9 $(lsof -i:7777 -t)
kill -9 $(lsof -i:8888 -t)
