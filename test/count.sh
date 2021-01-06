#!/bin/bash
# Count the number of lossless files

count="$(find . -name "*.flac" | wc -l)"

echo "$count"