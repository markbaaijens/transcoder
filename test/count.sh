#!/bin/bash
# Count the number of lossless files

count="$(find . -type f -name "*.flac" | wc -l)"

echo "$count"

rand=$(($RANDOM % $count))

echo "$rand"

readarray -d '' flacs < <(find . -type f -name "*.flac" -print0)

echo "${flacs[$rand]}"