#!/bin/sh

cd "$(dirname "$0")"

echo "running from $(pwd)"

./grades.py $@

cp ./test.png ../brady/
