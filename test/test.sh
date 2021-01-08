#!/bin/bash
# Presume: flacs are in $root/flac
# Note: all tests are idempotent

function given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_mp3_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    rm -rf $destination/*
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    if cat $root/$log_file | grep -q "transcoded to mp3: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_ogg_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/ogg"
    python3 ../transcoder.py $source --oggfolder $destination --logfolder $root/
    rm -f $root/$log_file

    rm -rf $destination/*
    python3 ../transcoder.py $source --oggfolder $destination --logfolder $root/
    
    if cat $root/$log_file | grep -q "transcoded to ogg: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.ogg" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_mp3_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' mp3s < <(find $destination -type f -name "*.mp3" -print0)
    rm -rf "${mp3s[0]}"

    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    
    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file
    
    readarray -d '' images < <(find $destination -type f -name "cover.jpg" -print0)
    image="${images[0]}"
    rm -rf "$image"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    searchstringlog=${image/$destination/"\- copying to \[mp3_tree\]"}
    if cat $root/$log_file | grep -q "$searchstringlog"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_changed_to_newer_date_of_flac_then_retranscode {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' flacs < <(find $source -type f -name "*.flac" -print0)
    touch "${flacs[0]}"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

root="./files"
log_file="transcoder.log"

given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_mp3_filecount
given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_ogg_filecount
given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_mp3_filecount
given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile
given_all_files_when_changed_to_newer_date_of_flac_then_retranscode
