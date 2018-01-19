#!/bin/bash

set -eu

export NOMAD_ADDR=http://localhost:4646

for job in $(nomad status| awk '{ print $1 }'|grep "-service"); do
	echo "stopping all $job tasks"
	curl -s $NOMAD_ADDR/v1/job/$job | jq '.TaskGroups[0].Count = 0 | {"Job": .}' | curl -s -X POST -d @- $NOMAD_ADDR/v1/job/$job
done

sleep 5
	
for job in $(nomad status| awk '{ print $1 }'|grep "-service"); do
	
	echo "start 1 $job task"
	curl -s $NOMAD_ADDR/v1/job/$job | jq '.TaskGroups[0].Count = 1 | {"Job": .}' | curl -s -X POST -d @- $NOMAD_ADDR/v1/job/$job
done
