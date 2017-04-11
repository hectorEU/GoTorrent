#!/bin/bash
kill -9 $(lsof -i:7969 -t)
