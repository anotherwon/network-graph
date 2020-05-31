#!/bin/sh

if [ "$(id -u)" -ne 0 ]; then
	printf "Error! Needs to be run as root!\n" >&2
	exit 1
fi

ip -json -details address
ip -json -details netns list-id
ip -all netns exec sh -c "ip -json -details address ; ip -json -details netns list-id"

