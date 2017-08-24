#!/bin/bash
find -user $UID -exec chmod g+rw {} \; -exec chown :topology {} \; 2>/dev/null
