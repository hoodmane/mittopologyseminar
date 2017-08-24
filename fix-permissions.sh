#!/bin/bash
find -not \( -path "./node_modules" -prune \) -not \( -path "./.git" -prune \)  -user $UID -exec chmod g+rw {} \; -exec chown :topology {} \; 2>/dev/null
