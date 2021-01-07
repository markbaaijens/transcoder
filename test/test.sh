#!/bin/bash
# Presume: flacs are in $root/flac
# Note: all tests are idempotent

function given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    rm -f $root/$log_file
    rm -rf $destination/*
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to mp3: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/ogg"
    rm -f $root/$log_file
    rm -rf $destination/*
    python3 ../transcoder.py $source --oggfolder $destination --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to ogg: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.ogg" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    
    count=$(find $destination -type f -name "*.mp3" | wc -l)
    if [[ $count -le 0 ]] ; then echo "No file to remove"; return 1; fi
    rand=$(($RANDOM % $count))
    readarray -d '' flacs < <(find $destination -type f -name "*.mp3" -print0)
    rm -f $root/$log_file

    # Picks a random MP3-file from the list of known files
    rm -rf "${flacs[$rand]}"
    echo "\"${flacs[$rand]}\" removed"
    
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    
    count=$(find $destination -type f -name "cover.jpg" | wc -l)
    if [[ $count -le 0 ]] ; then echo "No file to remove"; return 1; fi
    rand=$(($RANDOM % $count))
    readarray -d '' images < <(find $destination -type f -name "cover.jpg" -print0)
    rm -f $root/$log_file

    # Picks a random MP3-file from the list of known files
    image="${images[$rand]}"
    rm -rf $image
    echo "\"$image\" removed"
    test=${$image/""/$destination}
    echo "$test"

    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    if cat $root/$log_file | grep -q "\- copying to \[mp3_tree\]/Nightwish/Human II Nature/cover.jpg"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

root="./files"
log_file="transcoder.log"

#given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount
#given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount
#given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile
