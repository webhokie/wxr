#!/bin/bash

date
ps ef | fgrep `pwd` | fgrep test.py | fgrep -v fgrep | awk '{print $1}' | xargs kill -9
