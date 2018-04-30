#!/bin/bash

export groupname="topology"

chmod_dirs(){
    chmod g+srwx "$1" || echo "Unable to 'chmod g+rwx' $1"
    chown :"$groupname" "$1" || echo "Unable to 'chown :$groupname $1'"
}

export -f chmod_dirs
find -type d \! \( -perm -g=rwx -group "$groupname" \) -exec bash -c 'chmod_dirs "$0"' {} \; 2>/dev/null
