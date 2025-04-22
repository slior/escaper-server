#!/bin/bash

export PYTHONPATH=$PYTHONPATH:./server

# Run Python unit tests
python3 -m unittest discover -s server/tests -t server 