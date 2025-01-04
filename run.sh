#!/bin/sh
while true
do
  echo `date`
  python -m src.generate
  echo Waiting another 4 hours...
  sleep 14400
done
