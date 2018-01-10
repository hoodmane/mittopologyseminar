#!/bin/bash
# Finds files that have the wrong group ownership (should be g+w, owned by
# topology) and tries to take over ownership, using the assumption that you
# probably have write access to the directory, if not to the file. This will
# fail if you don't have write access to the directory.
export groupname="topology"

reown(){
    tmpfile="$1".tmp
    while [[ -e "$tmpfile" ]] ; do
        tmpfile="$tmpfile".tmp
    done
    if cp -a "$1" "$tmpfile" 2>/dev/null ; then
        if mv -f "$tmpfile" "$1" ; then
            # success
            chown :"$groupname" "$1"
            chmod g+rw "$1"
            echo "Fixed permissions on $1"
        else  # made copy but failed to move it into place
            rm "$tmpfile"
        fi
    else
        echo "Failed to change permissions on $1"
    fi
}

# need to export this so it can be used in a subshell in the find -exec
export -f reown

find -type f \! \( -perm -g=rw -group "$groupname" \) -exec bash -c 'reown "$0"' {} \; 2>/dev/null
