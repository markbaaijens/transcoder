#!/usr/bin/python
#
# File....: transcoder.py
# Authors.: Mark Baaijens
#

import time
import os
import subprocess
from fnmatch import fnmatch
import sys

# Define and init global counters
flacs_scanned_count = 0
mp3_transcoded_count = 0
ogg_transcoded_count = 0
cover_files_copied_count = 0
cover_embedded_count = 0
obsolete_files_deleted_count = 0
empty_folders_deleted_count = 0

# Constants
CONST_MP3 = 'mp3'
CONST_OGG = 'ogg'
CONST_LOG_FILENAME = 'mtranscoder.log'

def logFileName():
    logFileName = ''
    if (log_dir != ''):
        logFileName = os.path.join(log_dir,  CONST_LOG_FILENAME)
    return logFileName

def log(logText, raw=False, forceConsole=False):
  #
  # Log to a predefined log file.
  #
  if dry_run == 1:
    logText = '(dry-run) ' + logText

  # More compact logging: replace fulldirs with [source_tree], [mp3_tree] and [ogg_tree]
  if not raw:
    if ogg_tree != '':
      if ogg_tree in logText:
        logText = logText.replace(ogg_tree, '[ogg_tree]')

    if mp3_tree != '':
      if mp3_tree in logText:
        logText = logText.replace(mp3_tree, '[mp3_tree]')
    
    if source_tree != '':  # This replacement must be last to prevent double replacements
      if source_tree in logText:
        logText = logText.replace(source_tree, '[source_tree]')

  # Do not log to a file when log_dir is not defined
  if (logFileName() != ''):
    outputFile = open(logFileName(), 'a')
    outputFile.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + logText + '\n' )
    outputFile.close()

  # Show output to console
  if (show_verbose or forceConsole):
    print(logText)
    
  return

def transCodeFileCheck(inputFile):
  #
  # Check if given file must be transcoded or tags must be copied
  #

  # Compile directory and file name and do some checking for each 
  # supported lossless transcode format.
  if ogg_encoding == 1:    
    outputFile = os.path.splitext(inputFile)[0] + '.' + CONST_OGG  # Change extension
    outputFile = outputFile.replace(source_tree, ogg_tree)         # Change root of file tree
    
    # Check if outputFile exists
    if not os.path.exists(outputFile):
      transCodeFile(inputFile, outputFile, CONST_OGG)          
    else:  # Outputfile exists
      # Check if inputFile (flac) is newer than the file to be encoded
      if os.path.getmtime(inputFile) > os.path.getmtime(outputFile):
        transCodeFile(inputFile, outputFile, CONST_OGG)
        
  if mp3_encoding == 1:    
    outputFile = os.path.splitext(inputFile)[0] + '.' + CONST_MP3  # Change extension
    outputFile = outputFile.replace(source_tree, mp3_tree)         # Change root of file tree

    # Check if outputFile exists
    if not os.path.exists(outputFile):
      transCodeFile(inputFile, outputFile, CONST_MP3)      
    else:  # outputFile exists
      # Check if inputFile (flac) is newer than the file to be encoded
      if os.path.getmtime(inputFile) > os.path.getmtime(outputFile):
        transCodeFile(inputFile, outputFile, CONST_MP3) 
        
  return

def transCodeFile(inputFile, outputFile, transcodeFormat): 
  #
  # Transcodes a file. Folder structure will be copied from the lossless (flac) tree.
  # In the end, the lossy tree(s) is indentical to the lossless tree.
  #
  
  # Output is redirected to the target-tree.
  # Folder structure will be copied from the source-tree

  log('- transcoding file: "' + inputFile + '" to ' + transcodeFormat)

  if dry_run == 0:

    # Create parent folders if the target folder for the output file does not exist
    outputFilebasedir = os.path.split(outputFile)[0]
    if not os.path.exists(outputFilebasedir):
      # Make all intermediate-level directories needed to contain the leaf directory.
      os.makedirs(outputFilebasedir)

    # For oggvorbis-encoding
    if transcodeFormat == CONST_OGG:  
        transCodeFileOgg(inputFile, outputFile)    

    # For mp3-encoding
    if transcodeFormat == CONST_MP3:
        transCodeFileMp3(inputFile, outputFile)    
    
  return
    
def transCodeFileOgg(inputFile, outputFile): 
    #
    # Transcodes a file to ogg
    #
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    # Determine name of a *local* temporary ogg-file; this makes it easier for
    # rights management (Popen is suspect to be critical about this)
    tempOggFile = tempfile.gettempdir() + '/' + 'temp.ogg'  

    # Encoding from flac to oggvorbis
    # -q = quality
    # -o = outputFile
    # -Q = quiet
    # Important: 'silent' option is imperative for running this 
    # script through a scheduler (cron); not using this option results
    # in unpredictable behaviour!
    p = subprocess.Popen(["nice", "oggenc", inputFile, "-Q", "-q" + str(ogg_quality), "-o" + tempOggFile], stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
        log('- an error occured during transcoding')
        log('=>' + output) 

    # Now we are ready with transcoding; copy to file to the desired output directory
    copyfile(tempOggFile, outputFile) 

    # Remove the temporary file(s)    
    os.remove(tempOggFile)

    global ogg_transcoded_count
    ogg_transcoded_count +=1

    return
    
def transCodeFileMp3(inputFile, outputFile): 
    #
    # Transcodes a file to mp3
    #
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    # Determine name of a *local* temporary wav-file; this makes it easier for
    # rights management (Popen is suspect to be critical about this)
    tempWavFile = tempfile.gettempdir() + '/' + 'temp.wav'

    # Decode the flac input file to .wav b/c Lame cannot encode directly from flac
    # Important: 'silent' option is imperative for running this 
    # script through a scheduler (cron); not using this option results
    # in unpredictable behaviour!
    # -s silent    
    # -d decode
    # -f force overwrite
    p = subprocess.Popen(["nice", "flac", "-s", "-d", "-f", inputFile, '-o', tempWavFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
      log('- an error occured during decoding to .wav')
      log('=>' + output) 

    # Determine name of a *local* temporary MP3-file; this makes it easier for
    # rights management (Popen is suspect to be critical about this)
    tempMP3File = tempfile.gettempdir() + '/' + 'temp.mp3'
      
    # Encoding from wav to mp3
    # -h = high quality
    # -f = fast mode
    # -b = bitrate
    # Important: 'silent' option is imperative for running this 
    # script through a scheduler (cron); not using this option results
    # in unpredictable behaviour!    
    p = subprocess.Popen(["nice", "lame", "-f", "--silent", "--noreplaygain", "--id3v2-only", "-b" + str(mp3_bitrate), "--tt",  "dummy", tempWavFile, tempMP3File], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
      log('- an error occured during transcoding')
      log('=>' + output) 

    # Because the input flac file is decoded to wav, all metadata is lost.
    # We have to extract this metadata from the original flac file and
    # put it directly into the generated mp3 file.
    # We do this by calling copyTagsToTranscodedFileMp3 to copy all tags from the
    # flac file to the mp3 file. This can only be done if the mp3 file has a valid
    # id3 header. We can force this by adding a dummy tt argument (--tt dummy) during encoding.  
    copyTagsToTranscodedFileMp3(inputFile, tempMP3File)

    # Now we are ready with transcoding; copy to file to the desired output directory
    copyfile(tempMP3File, outputFile) 

    # Remove the temporary file(s)    
    os.remove(tempWavFile)
    os.remove(tempMP3File)
      
    global mp3_transcoded_count
    mp3_transcoded_count += 1
 
    return

def copyTagsToTranscodedFileMp3(losslessFile, lossyFile):  
  #
  # Copy the tags from the losslessFile (.flac) to the lossyFile.
  # All previous tags from the lossyFile will be deleted before the
  # tags from the losslessFile are copied.
  #
  from mutagen.flac import FLAC
  from mutagen.id3 import ID3   
  
  # Read all tags from the flac file
  flacFile = FLAC(losslessFile)
  flacFileTags = flacFile.tags # Returns a dictionary containing the flac tags
  
  # Only mp3 files with ID3 headers can be openend.
  # So be sure to add some tags during encoding .wav. to mp3
    
  # Mapping from Vorbis comments field recommendations to id3v2_4_0
  # For more information about vorbis field recommendations: http://reactor-core.org/ogg-tagging.html
  # For more information about id3v2_4_0 frames: http://www.id3.org/id3v2.4.0-frames
  #
  # Single value tags:
  #  ALBUM              -> TALB
  #  ARTIST             -> TPE1
  #  PUBLISHER          -> TPUB
  #  COPYRIGHT          -> WCOP
  #  DISCNUMBER         -> TPOS
  #  ISRC               -> TSRC
  #  EAN/UPN 
  #  LABEL              
  #  LABELNO 
  #  LICENSE             -> TOWN
  #  OPUS                -> TIT3
  #  SOURCEMEDIA         -> TMED
  #  TITLE               -> TIT2
  #  TRACKNUMBER         -> TRCK
  #  VERSION 
  #  ENCODED-BY          -> TENC
  #  ENCODING 
  # Multiple value tags:
  #  COMPOSER            -> TCOM
  #  ARRANGER 
  #  LYRICIST            -> TEXT 
  #  AUTHOR              -> TEXT
  #  CONDUCTOR           -> TPE3
  #  PERFORMER           -> 
  #  ENSEMBLE            -> TPE2
  #  PART                -> TIT1
  #  PARTNUMBER          -> TIT1
  #  GENRE               -> TCON
  #  DATE                -> TDRC
  #  LOCATION 
  #  COMMENT             -> COMM
  # Other vorbis tags are mapped to TXXX tags   
    
  mp3File = ID3(lossyFile)    
  mp3File.delete()    
      
  for key,value in flacFileTags.items():
    if key == 'title':
      # Map to TIT2 frame
      from mutagen.id3 import TIT2
      mp3File.add(TIT2(encoding=3, text=value)) 
    elif key == 'album':
      # Map to TALB frame
      from mutagen.id3 import TALB
      mp3File.add(TALB(encoding=3, text=value))
    elif key == 'artist':
      # Map to TPE1 frame
      from mutagen.id3 import TPE1
      mp3File.add(TPE1(encoding=3, text=value)) 
    elif key == 'tracknumber':
      # Map to TRCK frame
      from mutagen.id3 import TRCK
      mp3File.add(TRCK(encoding=3, text=value))
    elif key == 'date':
      # Map to TDRC frame
      from mutagen.id3 import TDRC
      mp3File.add(TDRC(encoding=3, text=value))
    elif key == 'genre':
      # Map to TCON frame
      from mutagen.id3 import TCON
      mp3File.add(TCON(encoding=3, text=value))
    elif key == 'discnumber':
      # Map to TPOS frame
      from mutagen.id3 import TPOS
      mp3File.add(TPOS(encoding=3, text=value))
    elif key == 'composer':
      # Map to TCOM frame
      from mutagen.id3 import TCOM
      mp3File.add(TCOM(encoding=3, text=value))
    elif key == 'conductor':
      # Map to TPE3 frame
      from mutagen.id3 import TPE3
      mp3File.add(TPE3(encoding=3, text=value))
    elif key == 'ensemble':
      # Map to TPE2 frame
      from mutagen.id3 import TPE2
      mp3File.add(TPE2(encoding=3, text=value))      
    elif key == 'comment':
      # Map to COMM frame
      from mutagen.id3 import COMM
      mp3File.add(COMM(encoding=3, text=value))
    elif key == 'publisher':
      # Map to TPUB frame
      from mutagen.id3 import TPUB
      mp3File.add(TPUB(encoding=3, text=value))
    elif key == 'opus':
      # Map to TIT3 frame
      from mutagen.id3 import TIT3
      mp3File.add(TIT3(encoding=3, text=value))
    elif key == 'sourcemedia':
      # Map to TMED frame
      from mutagen.id3 import TMED
      mp3File.add(TMED(encoding=3, text=value))
    elif key == 'isrc':
      # Map to TSRC frame
      from mutagen.id3 import TSRC
      mp3File.add(TSRC(encoding=3, text=value))
    elif key == 'license':
      # Map to TOWN frame
      from mutagen.id3 import TOWN
      mp3File.add(TOWN(encoding=3, text=value))
    elif key == 'copyright':
      # Map to WCOP frame
      from mutagen.id3 import WCOP
      mp3File.add(WCOP(encoding=3, text=value))
    elif key == 'encoded-by':
      # Map to TENC frame
      from mutagen.id3 import TENC
      mp3File.add(TENC(encoding=3, text=value))
    elif (key == 'part' or key == 'partnumber'):
      # Map to TIT3 frame
      from mutagen.id3 import TIT3
      mp3File.add(TIT3(encoding=3, text=value))
    elif (key == 'lyricist' or key == 'textwriter'):
      # Map to TEXT frame
      from mutagen.id3 import TIT3
      mp3File.add(TIT3(encoding=3, text=value))
    else: #all other tags are mapped to TXXX frames
      # Map to TXXX frame
      from mutagen.id3 import TXXX
      mp3File.add(TXXX(encoding=3, text=value, desc=key))        
  
    mp3File.update_to_v24()
    mp3File.save() 
    
  return

def cleanupLossyTree(lossyTree, lossyFormat):
  #
  # Remove unwanted files in the losst tree 
  #
  log('Cleanup ' + lossyTree) 
  global obsolete_files_deleted_count 

  for dir, dirnames, fileNames in os.walk(lossyTree, topdown=False): # Note the topdown       
    for fileName in fileNames:
      # Check for transcoded files
      if fnmatch(fileName, '*.' + lossyFormat): # We have a transcoded file          
        lossyFile = os.path.join(dir, fileName) # The full pathname of the lossy file
        
        # Derive the sourceFile
        sourcePath = dir.replace(lossyTree, source_tree)        
        sourceFile = os.path.join(sourcePath,fileName)        
        sourceFile = os.path.splitext(sourceFile)[0] + '.flac' # Change extension   

        # Check if there exists a corresponding sourceFile
        if not os.path.isfile(sourceFile):                              
          if dry_run == 0:
            os.remove(lossyFile)
          log('- file deleted: ' + lossyFile)
          obsolete_files_deleted_count  += 1
      else: # Found a file but not a transcoded one
        # Check for transcoded files
        if fnmatch(fileName, '*.*'): # We have a not-transcoded file          
          lossyFile = os.path.join(dir, fileName) # The full pathname of the lossy file
        
          # Derive the sourceFile
          sourcePath = dir.replace(lossyTree, source_tree)        
          sourceFile = os.path.join(sourcePath,fileName)        

          # Check if there exists a corresponding sourceFile
          if not os.path.isfile(sourceFile):                              
            if dry_run == 0:
              os.remove(lossyFile)
            log('- file deleted: ' + lossyFile)
            obsolete_files_deleted_count  += 1

  # Remove empty directories, first the child directories
  removeEmptyDirectories(lossyTree)

  # Do it twice to also remove empty parent directories
  removeEmptyDirectories(lossyTree)

  return

def removeEmptyDirectories(tree):

  # Remove empty directories
  for dir, dirnames, fileNames in os.walk(tree, topdown=False):
    if len(dirnames) == 0 and len(fileNames) == 0:
      if dir != tree:  # Never remove the top dir!   
        if dry_run == 0:
          os.rmdir(dir)
        log('- directory removed: ' + dir) 
        global empty_folders_deleted_count
        empty_folders_deleted_count +=1

  return

def transCodeFiles():
  #
  # Transcode all files; wrapper for transCodeFile()
  #
  log('Transcode files')

  if (ogg_encoding == 0 and mp3_encoding == 0):
    log('- no transcoding to ogg or mp3 is set; nothing to do')
    return

  for dir, dirnames, fileNames in os.walk(source_tree):
    for fileName in sorted(fileNames):
      sourceFileFullPathName = os.path.join(dir, fileName)
      if fnmatch(sourceFileFullPathName, "*.flac"):
        global flacs_scanned_count
        flacs_scanned_count += 1
        transCodeFileCheck(sourceFileFullPathName)  

  return

def copyCoverFiles(lossyTree):
  #
  # Copy cover files from flac- to lossy-tree(s); embed album art into transcoded file
  #
  from shutil import copyfile # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
  from math import trunc 
  
  log('Copy cover files to lossy tree: ' + lossyTree)
  for dir, dirnames, fileNames in os.walk(source_tree):
    for fileName in sorted(fileNames):
      sourceCoverFullFileName = os.path.join(dir, fileName)
      if fnmatch(sourceCoverFullFileName, "*/cover.jpg"):

        # Only copy file when (1) target cover file does not exit or (2) target cover file is older
        copyFile = False
        lossyCoverFullFileName = sourceCoverFullFileName.replace(source_tree, lossyTree)  
        if not os.path.isfile(lossyCoverFullFileName):   # Check if target file does not exist 
          copyFile = True
        else:
          # Check if source cover file is newer than target; using trunc to avoid to precise comparison
          if trunc(os.path.getmtime(sourceCoverFullFileName)) > trunc(os.path.getmtime(lossyCoverFullFileName)): 
            copyFile = True

        if copyFile:
          log('- copying ' + sourceCoverFullFileName + ' to ' + lossyCoverFullFileName) 
          global cover_files_copied_count
          cover_files_copied_count += 1

          if dry_run == 0:
            # Create intermediate-level directories in the output tree; normally, these already exist
            # because during transcoding they will be created; but this is 'just in case'
            outputFileBaseDir = os.path.split(lossyCoverFullFileName)[0]
            if not os.path.exists(outputFileBaseDir):
              # Make all intermediate-level directories needed to contain the leaf directory.
              os.makedirs(outputFileBaseDir)       

            # Copy the cover file
            copyfile(sourceCoverFullFileName, lossyCoverFullFileName) 

            global cover_embedded_count
            # Embed image in each audio file in the current dir
            for fileName in os.listdir(outputFileBaseDir):
                lossyFileFullFileName = os.path.join(outputFileBaseDir,  fileName)  
                if os.path.splitext(fileName)[1] ==  '.' + CONST_MP3:
                    updateCoverMp3(lossyFileFullFileName, sourceCoverFullFileName)
                    cover_embedded_count += 1
                if os.path.splitext(fileName)[1] == '.' + CONST_OGG:
                    updateCoverOgg(lossyFileFullFileName, sourceCoverFullFileName)                    
                    cover_embedded_count += 1
  return  

def updateCoverMp3(lossyFileName, artworkFileName):   
    #
    # Embed album art into transcoded file: MP3
    #
    from mutagen.id3 import ID3, APIC
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    log('- embedding album art ' + artworkFileName + ' to ' + lossyFileName) 

    # Copy lossy file to a local location; to prevent (save) errors in a samba environment
    tempLossyFile = tempfile.gettempdir() + '/' + 'temp.mp3'
    copyfile(lossyFileName, tempLossyFile) 

    # Embed the image
    audio = ID3(tempLossyFile)
    with open(artworkFileName, 'rb') as albumart:
        audio['APIC'] = APIC(
                      encoding=3,
                      mime='image/jpeg',
                      type=3, desc=u'cover',
                      data=albumart.read())
    audio.save()

    # Now we are ready; copy the file to the desired output directory
    copyfile(tempLossyFile, lossyFileName) 
    os.remove(tempLossyFile)  # Remove the temporary file(s)    

    return

def updateCoverOgg(lossyFileName, artworkFileName):   
    #
    # Embed album art into transcoded file: OGG
    #
    import base64; from mutagen.oggvorbis import OggVorbis; 
    from mutagen.flac import Picture; import PIL.Image; 
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
    
    log('- embedding album art ' + artworkFileName + ' to ' + lossyFileName) 

    # Copy lossy file to a local location; to prevent (save) errors in a samba environment
    tempLossyFile = tempfile.gettempdir() + '/' + 'temp.ogg'
    copyfile(lossyFileName, tempLossyFile) 

    # Embed the image
    o=OggVorbis(tempLossyFile);

    im = PIL.Image.open(artworkFileName);
    w,h = im.size; 
    
    p = Picture(); 
    imdata = open(artworkFileName,'rb').read();
    p.data = imdata; 
    p.type = 3; 
    p.desc = ''; 
    p.mime = 'image/jpeg';
    p.width = w; 
    p.height = h; 
    p.depth = 24; 
    
    dt = p.write(); 
    enc = base64.b64encode(dt).decode('ascii');
    o['metadata_block_picture'] = [enc];
    o.save()   

    # Now we are ready; copy the file to the desired output directory
    copyfile(tempLossyFile, lossyFileName) 
    os.remove(tempLossyFile)  # Remove the temporary file(s)  
    
    return

def sanitizeFileName(fileName):
    # Check if the last character is a trailing / or \
    if (fileName[-1:] in ['/', '\\']):
        fileName = fileName[:-1]  # Strip the last character
    return fileName

#
# Body
#

# Define global settings and give them some sensible defaults
source_tree=''
ogg_tree=''
ogg_quality=1
mp3_tree=''
mp3_bitrate=128
dry_run=0
log_dir=''
show_verbose = 0

#
# Parse command line arguments
#
import argparse
parser = argparse.ArgumentParser(description='Transcode lossless audio files (flac) to lossy formats (mp3/ogg).')

parser.add_argument('sourcefolder', metavar='sourcefolder', type=str, help='folder containing source files (flac)')
parser.add_argument('-v', '--verbose', help="increase output verbosity; show (more) output to console", action="store_true")
parser.add_argument('-d', '--dry-run', help="perform a trial run with no changes made",  action="store_true")        
parser.add_argument('--logfolder', type=str,  help="folder where log (= mtranscoder.log) is stored; no folder is no logging",  nargs=1) 
parser.add_argument('--mp3folder', type=str,  help="folder where transcoded mp3's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
parser.add_argument('--mp3bitrate', type=int,  help="quality of the transcoded ogg files; default is 128",  nargs=1,  choices=[128, 256, 384]) 
parser.add_argument('--oggfolder', type=str,  help="folder where transcoded ogg's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
parser.add_argument('--oggquality', type=int,  help="quality of the transcoded ogg files; default is 1",  nargs=1,  choices=[1, 2, 3, 4, 5]) 

args = parser.parse_args()

# Pass command line argument(s) to setting variable(s)
show_verbose = args.verbose
dry_run = args.dry_run
source_tree = sanitizeFileName(args.sourcefolder)

# --logfolder is optional
if (args.logfolder != None) :
    if (args.logfolder[0] != ''):
        log_dir = args.logfolder[0]
log_dir = sanitizeFileName(log_dir)   

# --mp3folder is optional
if (args.mp3folder != None) :
    if (args.mp3folder[0] != ''):
        mp3_tree = args.mp3folder[0]
mp3_tree = sanitizeFileName(mp3_tree)

# --oggfolder is optional
if (args.oggfolder != None) :
    if (args.oggfolder[0] != ''):
        ogg_tree = args.oggfolder[0]
ogg_tree = sanitizeFileName(ogg_tree)
        
# --oggquality is optional
if (args.oggquality != None) :
    if (args.oggquality[0] != ''):
        ogg_quality = args.oggquality[0]

# --mp3bitrate is optional
if (args.mp3bitrate != None) :
    if (args.mp3bitrate[0] != ''):
        mp3_bitrate = args.mp3bitrate[0]

# Calculate derived variables
ogg_encoding = 0
if ogg_tree  !='':
  ogg_encoding = 1

mp3_encoding = 0
if mp3_tree != '':
  mp3_encoding = 1

# Check if log location is valid
if (log_dir != ''):
  if not os.path.exists(log_dir):
    # When the logdir is invalid, we cannot write to a log obviously; so just print the 
    # error to the console
    print('Location of log_dir = ' + log_dir + ' is not valid. Abort.')
    sys.exit(1)

# Check if file trees are valid
if (source_tree != ''):
  if not os.path.exists(source_tree):
    log('Location of source_tree = ' + source_tree + ' is not valid. Abort.', True, True)
    sys.exit(1)

if ogg_encoding == 1:
  if not os.path.exists(ogg_tree):
    log('Location of ogg_tree = ' + ogg_tree + ' is not valid. Abort.', True, True)
    sys.exit(1)

if mp3_encoding == 1:
  if not os.path.exists(mp3_tree):
    log('Location of mp3_tree = ' + mp3_tree + ' is not valid. Abort.', True, True)
    sys.exit(1)

# Check if there's another process running; if so, bail out...
lockfile = '/tmp/mtranscoder.lock'
if os.path.exists(lockfile):
  log('Another process is running: lockfile ' + lockfile + ' found ("rm ' + lockfile + '" to continue). Abort.', True, True)
  sys.exit(1)

# This shouldn't happen on previous exit, though it should on users Crtl+C
import atexit
atexit.register(os.remove, lockfile)

# Give a hint for seeing progress
if (log_dir == '') and (not show_verbose):
  print('Hint: to monitor progress, use --verbose or --logfolder (or both)')

# Start logging
log('Start session')

log('- source_tree: ' + source_tree, True)
log('- dry_run: ' + str(dry_run))
log('- show_verbose: ' + str(show_verbose))

logText = '- ogg_tree: ' + ogg_tree
if (ogg_tree == ''):
    logText += '(empty) => no transcoding'
log(logText, True)
if (ogg_tree != ''):
    log('- ogg_quality: ' + str(ogg_quality))

logText = '- mp3_tree: ' + mp3_tree
if (mp3_tree == ''):
    logText += '(empty) => no transcoding'
log(logText, True)
if (mp3_tree != ''):
    log('- mp3_bitrate: ' + str(mp3_bitrate))

logText = '- logging to: ' + logFileName()
if (logFileName() == ''):
    logText += '(empty) => no logging'
log(logText)    

# Place lock file 
outputFile = open(lockfile,'w')
outputFile.write('lock')
outputFile.close()

# Scan all files in source_tree, check every individual file if it needs
# transcoding or tag synchronizing.
transCodeFiles()
      
# Copy all cover files to the lossy tree(s)
if ogg_encoding == 1:
  copyCoverFiles(ogg_tree)
if mp3_encoding == 1:
  copyCoverFiles(mp3_tree)

# Scan all files in lossy trees. Delete or remove them if there is no
# corresponding flac file
if ogg_encoding == 1:
  cleanupLossyTree(ogg_tree, CONST_OGG)
if mp3_encoding == 1:
  cleanupLossyTree(mp3_tree, CONST_MP3)

# Show summary
log('Summary')
log('- flacs scanned: ' + str(flacs_scanned_count))
log('- transcoded to mp3: ' + str(mp3_transcoded_count))
log('- transcoded to ogg: ' + str(ogg_transcoded_count))
log('- cover files copied: ' + str(cover_files_copied_count))
log('- covers embedded in files: ' + str(cover_embedded_count))
log('- obsolete files deleted: ' + str(obsolete_files_deleted_count))
log('- empty folders deleted: ' + str(empty_folders_deleted_count))

# Stop logging
log('End session')
sys.exit(0)
