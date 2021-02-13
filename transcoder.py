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
flacsScannedCount = 0
mp3TranscodedCount = 0
oggTranscodedCount = 0
coverFilesCopiedCount = 0
coverEmbeddedCount = 0
obsoleteFilesDeletedCount = 0
emptyFoldersDeletedCount = 0

# Constants
constMp3 = 'mp3'
constOgg = 'ogg'
constLogFileName = 'transcoder.log'

def LogFileName():
    logFileName = ''
    if (logDir != ''):
        logFileName = os.path.join(logDir,  constLogFileName)
    return logFileName

def Log(logText, raw=False, forceConsole=False):
  #
  # Log to a predefined log file.
  #
  if dryRun == 1:
    logText = '(dry-run) ' + logText

  # More compact logging: replace fulldirs with [source_tree], [mp3_tree] and [ogg_tree]
  if not raw:
    if oggTree != '':
      if oggTree in logText:
        logText = logText.replace(oggTree, '[ogg_tree]')

    if mp3Tree != '':
      if mp3Tree in logText:
        logText = logText.replace(mp3Tree, '[mp3_tree]')
    
    if sourceTree != '':  # This replacement must be last to prevent double replacements
      if sourceTree in logText:
        logText = logText.replace(sourceTree, '[source_tree]')

  # Do not log to a file when log_dir is not defined
  if (LogFileName() != ''):
    outputFile = open(LogFileName(), 'a')
    outputFile.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + logText + '\n' )
    outputFile.close()

  # Show output to console
  if (showVerbose or forceConsole):
    print(logText)
    
  return

def TransCodeFileCheck(inputFile):
  #
  # Check if given file must be transcoded or tags must be copied
  #

  # Compile directory and file name and do some checking for each 
  # supported lossless transcode format.
  if oggEncoding == 1:    
    outputFile = os.path.splitext(inputFile)[0] + '.' + constOgg  # Change extension
    outputFile = outputFile.replace(sourceTree, oggTree)         # Change root of file tree
    
    # Check if outputFile exists
    if not os.path.exists(outputFile):
      TransCodeFile(inputFile, outputFile, constOgg)
    else:  # Outputfile exists
      # Check if inputFile (flac) is newer than the file to be encoded
      if os.path.getmtime(inputFile) > os.path.getmtime(outputFile):
        TransCodeFile(inputFile, outputFile, constOgg)

  if mp3Encoding == 1:    
    outputFile = os.path.splitext(inputFile)[0] + '.' + constMp3  # Change extension
    outputFile = outputFile.replace(sourceTree, mp3Tree)         # Change root of file tree

    # Check if outputFile exists
    if not os.path.exists(outputFile):
      TransCodeFile(inputFile, outputFile, constMp3)
    else:  # outputFile exists
      # Check if inputFile (flac) is newer than the file to be encoded
      if os.path.getmtime(inputFile) > os.path.getmtime(outputFile):
        TransCodeFile(inputFile, outputFile, constMp3)      
        
  return


def TransCodeFile(inputFile, outputFile, transcodeFormat): 
  #
  # Transcodes a file. Folder structure will be copied from the lossless (flac) tree.
  # In the end, the lossy tree(s) is indentical to the lossless tree.
  #
  
  # Output is redirected to the target-tree.
  # Folder structure will be copied from the source-tree

  Log('- transcoding file: "' + inputFile + '" to ' + transcodeFormat)

  if dryRun == 0:

    # Create parent folders if the target folder for the output file does not exist
    outputFilebasedir = os.path.split(outputFile)[0]
    if not os.path.exists(outputFilebasedir):
      # Make all intermediate-level directories needed to contain the leaf directory.
      os.makedirs(outputFilebasedir)

    # For oggvorbis-encoding
    if transcodeFormat == constOgg:  
        TransCodeFileOgg(inputFile, outputFile)    

    # For mp3-encoding
    if transcodeFormat == constMp3:
        TransCodeFileMp3(inputFile, outputFile)

    if os.path.exists(outputFilebasedir + "/cover.jpg"):
        os.remove(outputFilebasedir + "/cover.jpg")
    
  return
    
def TransCodeFileOgg(inputFile, outputFile): 
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
    p = subprocess.Popen(["nice", "oggenc", inputFile, "-Q", "-q" + str(oggQuality), "-o" + tempOggFile], stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
        Log('- an error occured during transcoding')
        Log('=>' + output) 

    # Now we are ready with transcoding; copy to file to the desired output directory
    copyfile(tempOggFile, outputFile) 

    # Remove the temporary file(s)    
    os.remove(tempOggFile)

    global oggTranscodedCount
    oggTranscodedCount +=1

    return
    
def TransCodeFileMp3(inputFile, outputFile): 
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
      Log('- an error occured during decoding to .wav')
      Log('=>' + output) 

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
    p = subprocess.Popen(["nice", "lame", "-f", "--silent", "--noreplaygain", "--id3v2-only", "-b" + str(mp3Bitrate), "--tt",  "dummy", tempWavFile, tempMP3File], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
      Log('- an error occured during transcoding')
      Log('=>' + output) 

    # Because the input flac file is decoded to wav, all metadata is lost.
    # We have to extract this metadata from the original flac file and
    # put it directly into the generated mp3 file.
    # We do this by calling copyTagsToTranscodedFileMp3 to copy all tags from the
    # flac file to the mp3 file. This can only be done if the mp3 file has a valid
    # id3 header. We can force this by adding a dummy tt argument (--tt dummy) during encoding.  
    CopyTagsToTranscodedFileMp3(inputFile, tempMP3File)

    # Now we are ready with transcoding; copy to file to the desired output directory
    copyfile(tempMP3File, outputFile) 

    # Remove the temporary file(s)    
    os.remove(tempWavFile)
    os.remove(tempMP3File)
      
    global mp3TranscodedCount
    mp3TranscodedCount += 1
 
    return

def CopyTagsToTranscodedFileMp3(losslessFile, lossyFile):  
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

def CleanUpLossyTree(lossyTree, lossyFormat):
  #
  # Remove unwanted files in the losst tree 
  #
  Log('Cleanup ' + lossyTree) 
  global obsoleteFilesDeletedCount 

  for dir, dirNames, fileNames in os.walk(lossyTree, topdown=False): # Note the topdown
    dirNames.sort()

    for fileName in sorted(fileNames):
      # Check for transcoded files
      if fnmatch(fileName, '*.' + lossyFormat): # We have a transcoded file          
        lossyFile = os.path.join(dir, fileName) # The full pathname of the lossy file
        
        # Derive the sourceFile
        sourcePath = dir.replace(lossyTree, sourceTree)        
        sourceFile = os.path.join(sourcePath, fileName)        
        sourceFile = os.path.splitext(sourceFile)[0] + '.flac' # Change extension   

        # Check if there exists a corresponding sourceFile
        if not os.path.isfile(sourceFile):                              
          if dryRun == 0:
            os.remove(lossyFile)
          Log('- file deleted: ' + lossyFile)
          obsoleteFilesDeletedCount  += 1
      else: # Found a file but not a transcoded one
        # Check for transcoded files
        if fnmatch(fileName, '*.*'): # We have a not-transcoded file          
          lossyFile = os.path.join(dir, fileName) # The full pathname of the lossy file
        
          # Derive the sourceFile
          sourcePath = dir.replace(lossyTree, sourceTree)        
          sourceFile = os.path.join(sourcePath, fileName)        

          # Check if there exists a corresponding sourceFile
          if not os.path.isfile(sourceFile):                              
            if dryRun == 0:
              os.remove(lossyFile)
            Log('- file deleted: ' + lossyFile)
            obsoleteFilesDeletedCount  += 1

  # Remove empty directories, first the child directories
  RemoveEmptyDirectories(lossyTree)

  # Do it twice to also remove empty parent directories
  RemoveEmptyDirectories(lossyTree)

  return

def RemoveEmptyDirectories(tree):

  # Remove empty directories
  for dir, dirNames, fileNames in os.walk(tree, topdown=False):
    dirNames.sort()
    
    if len(dirNames) == 0 and len(fileNames) == 0:
      if dir != tree:  # Never remove the top dir!   
        if dryRun == 0:
          os.rmdir(dir)
        Log('- directory removed: ' + dir) 
        global emptyFoldersDeletedCount
        emptyFoldersDeletedCount +=1

  return

def TransCodeFiles():
  #
  # Transcode all files; wrapper for transCodeFile()
  #
  Log('Transcode files')

  if (oggEncoding == 0 and mp3Encoding == 0):
    Log('- no transcoding to ogg or mp3 is set; nothing to do')
    return

  for dir, dirNames, fileNames in os.walk(sourceTree):
    dirNames.sort()

    for fileName in sorted(fileNames):
      sourceFileFullPathName = os.path.join(dir, fileName)
      if fnmatch(sourceFileFullPathName, "*.flac"):
        global flacsScannedCount
        flacsScannedCount += 1
        TransCodeFileCheck(sourceFileFullPathName)  

  return

def CopyCoverFiles(lossyTree):
  #
  # Copy cover files from flac- to lossy-tree(s); embed album art into transcoded file
  #
  from shutil import copyfile # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
  from math import trunc 
  
  Log('Copy cover files to lossy tree: ' + lossyTree)
  for dir, dirNames, fileNames in os.walk(sourceTree):
    dirNames.sort()

    for fileName in sorted(fileNames):
      sourceCoverFullFileName = os.path.join(dir, fileName)
      if fnmatch(sourceCoverFullFileName, "*/cover.jpg"):

        # Only copy file when:
        # (1) target cover file does not exit
        # (2) target cover file is older
        copyFile = False
        lossyCoverFullFileName = sourceCoverFullFileName.replace(sourceTree, lossyTree)  
        if not os.path.isfile(lossyCoverFullFileName):   # Check if target file does not exist 
          copyFile = True
        else:
          # Check if source cover file is newer than target
          if os.path.getmtime(sourceCoverFullFileName) > os.path.getmtime(lossyCoverFullFileName): 
            copyFile = True

        if copyFile:
          Log('- copying to ' + lossyCoverFullFileName) 
          global coverFilesCopiedCount
          coverFilesCopiedCount += 1

          if dryRun == 0:
            # Create intermediate-level directories in the output tree; normally, these already exist
            # because during transcoding they will be created; but this is 'just in case'
            outputFileBaseDir = os.path.split(lossyCoverFullFileName)[0]
            if not os.path.exists(outputFileBaseDir):
              # Make all intermediate-level directories needed to contain the leaf directory.
              os.makedirs(outputFileBaseDir)       

            # Copy the cover file
            copyfile(sourceCoverFullFileName, lossyCoverFullFileName) 

            global coverEmbeddedCount
            # Embed image in each audio file in the current dir
            for fileName in sorted(os.listdir(outputFileBaseDir)):
                lossyFileFullFileName = os.path.join(outputFileBaseDir,  fileName)  
                if os.path.splitext(fileName)[1] ==  '.' + constMp3:
                    UpdateCoverMp3(lossyFileFullFileName, sourceCoverFullFileName)
                    coverEmbeddedCount += 1
                if os.path.splitext(fileName)[1] == '.' + constOgg:
                    UpdateCoverOgg(lossyFileFullFileName, sourceCoverFullFileName)                    
                    coverEmbeddedCount += 1
  return  

def UpdateCoverMp3(lossyFileName, artworkFileName):   
    #
    # Embed album art into transcoded file: MP3
    #
    from mutagen.id3 import ID3, APIC
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    Log('- embedding album art in ' + lossyFileName) 

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

def UpdateCoverOgg(lossyFileName, artworkFileName):   
    #
    # Embed album art into transcoded file: OGG
    #
    import base64; from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import Picture; import PIL.Image
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
    
    Log('- embedding album art in ' + lossyFileName) 

    # Copy lossy file to a local location; to prevent (save) errors in a samba environment
    tempLossyFile = tempfile.gettempdir() + '/' + 'temp.ogg'
    copyfile(lossyFileName, tempLossyFile) 

    # Embed the image
    o=OggVorbis(tempLossyFile)

    im = PIL.Image.open(artworkFileName)
    w,h = im.size
    
    p = Picture()
    imdata = open(artworkFileName,'rb').read()
    p.data = imdata
    p.type = 3
    p.desc = ''
    p.mime = 'image/jpeg'
    p.width = w
    p.height = h
    p.depth = 24
    
    dt = p.write()
    enc = base64.b64encode(dt).decode('ascii')
    o['metadata_block_picture'] = [enc]
    o.save()   

    # Now we are ready; copy the file to the desired output directory
    copyfile(tempLossyFile, lossyFileName) 
    os.remove(tempLossyFile)  # Remove the temporary file(s)  
    
    return

def SanitizeFileName(fileName):
    # Check if the last character is a trailing / or \
    if (fileName[-1:] in ['/', '\\']):
        fileName = fileName[:-1]  # Strip the last character
    return fileName

#
# Body
#

# Define global settings and give them some sensible defaults
sourceTree=''
oggTree=''
oggQuality=1
mp3Tree=''
mp3Bitrate=128
dryRun=0
logDir=''
showVerbose = 0

#
# Parse command line arguments
#
import argparse
parser = argparse.ArgumentParser(description='Transcode lossless audio files (flac) to lossy formats (mp3/ogg).')

parser.add_argument('sourcefolder', metavar='sourcefolder', type=str, help='folder containing source files (flac)')
parser.add_argument('-v', '--verbose', help="increase output verbosity; show (more) output to console", action="store_true")
parser.add_argument('-d', '--dry-run', help="perform a trial run with no changes made",  action="store_true")        
parser.add_argument('--logfolder', type=str,  help="folder where log (= transcoder.log) is stored; no folder is no logging",  nargs=1) 
parser.add_argument('--mp3folder', type=str,  help="folder where transcoded mp3's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
parser.add_argument('--mp3bitrate', type=int,  help="quality of the transcoded ogg files; default is 128",  nargs=1,  choices=[128, 256, 384]) 
parser.add_argument('--oggfolder', type=str,  help="folder where transcoded ogg's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
parser.add_argument('--oggquality', type=int,  help="quality of the transcoded ogg files; default is 1",  nargs=1,  choices=[1, 2, 3, 4, 5]) 

args = parser.parse_args()

# Pass command line argument(s) to setting variable(s)
showVerbose = args.verbose
dryRun = args.dry_run
sourceTree = SanitizeFileName(args.sourcefolder)

# --logfolder is optional
if (args.logfolder != None) :
    if (args.logfolder[0] != ''):
        logDir = args.logfolder[0]
logDir = SanitizeFileName(logDir)   

# --mp3folder is optional
if (args.mp3folder != None) :
    if (args.mp3folder[0] != ''):
        mp3Tree = args.mp3folder[0]
mp3Tree = SanitizeFileName(mp3Tree)

# --oggfolder is optional
if (args.oggfolder != None) :
    if (args.oggfolder[0] != ''):
        oggTree = args.oggfolder[0]
oggTree = SanitizeFileName(oggTree)
        
# --oggquality is optional
if (args.oggquality != None) :
    if (args.oggquality[0] != ''):
        oggQuality = args.oggquality[0]

# --mp3bitrate is optional
if (args.mp3bitrate != None) :
    if (args.mp3bitrate[0] != ''):
        mp3Bitrate = args.mp3bitrate[0]

# Calculate derived variables
oggEncoding = 0
if oggTree  !='':
  oggEncoding = 1

mp3Encoding = 0
if mp3Tree != '':
  mp3Encoding = 1

# Check if log location is valid
if (logDir != ''):
  if not os.path.exists(logDir):
    # When the logdir is invalid, we cannot write to a log obviously; so just print the 
    # error to the console
    print('Location of log_dir = ' + logDir + ' is not valid. Abort.')
    sys.exit(1)

# Check if file trees are valid
if (sourceTree != ''):
  if not os.path.exists(sourceTree):
    Log('Location of source_tree = ' + sourceTree + ' is not valid. Abort.', True, True)
    sys.exit(1)

if oggEncoding == 1:
  if not os.path.exists(oggTree):
    Log('Location of ogg_tree = ' + oggTree + ' is not valid. Abort.', True, True)
    sys.exit(1)

if mp3Encoding == 1:
  if not os.path.exists(mp3Tree):
    Log('Location of mp3_tree = ' + mp3Tree + ' is not valid. Abort.', True, True)
    sys.exit(1)

# Check via existence of a lockfile, if there's another process running; if so, bail out...
lockfile = '/tmp/transcoder.lock'
if os.path.exists(lockfile):
  Log('Starting transcoder. But another process is still running, lockfile found ("rm ' + lockfile + '" to continue). Abort.', True, True)
  sys.exit(1)

# Remove lockfile on exit, even when the user hits Crtl+C
import atexit
atexit.register(os.remove, lockfile)

# Place lock file 
outputFile = open(lockfile,'w')
outputFile.write('lock')
outputFile.close()

# Give a hint for seeing progress
if (logDir == '') and (not showVerbose):
  print('Hint: to monitor progress, use --verbose or --logfolder (or both)')

# Start logging
Log('Start session')

Log('- source_tree: ' + sourceTree, True)
Log('- dry_run: ' + str(dryRun))
Log('- show_verbose: ' + str(showVerbose))

logText = '- ogg_tree: ' + oggTree
if (oggTree == ''):
    logText += '(empty) => no transcoding'
Log(logText, True)
if (oggTree != ''):
    Log('- ogg_quality: ' + str(oggQuality))

logText = '- mp3_tree: ' + mp3Tree
if (mp3Tree == ''):
    logText += '(empty) => no transcoding'
Log(logText, True)
if (mp3Tree != ''):
    Log('- mp3_bitrate: ' + str(mp3Bitrate))

logText = '- logging to: ' + LogFileName()
if (LogFileName() == ''):
    logText += '(empty) => no logging'
Log(logText)    

# Scan all files in source_tree, check every individual file if it needs
# transcoding or tag synchronizing.
TransCodeFiles()
      
# Copy all cover files to the lossy tree(s)
if oggEncoding == 1:
  CopyCoverFiles(oggTree)
if mp3Encoding == 1:
  CopyCoverFiles(mp3Tree)

# Scan all files in lossy trees. Delete or remove them if there is no
# corresponding flac file
if oggEncoding == 1:
  CleanUpLossyTree(oggTree, constOgg)
if mp3Encoding == 1:
  CleanUpLossyTree(mp3Tree, constMp3)

# Show summary
Log('Summary')
Log('- flacs scanned: ' + str(flacsScannedCount))
Log('- transcoded to mp3: ' + str(mp3TranscodedCount))
Log('- transcoded to ogg: ' + str(oggTranscodedCount))
Log('- cover files copied: ' + str(coverFilesCopiedCount))
Log('- covers embedded in files: ' + str(coverEmbeddedCount))
Log('- obsolete files deleted: ' + str(obsoleteFilesDeletedCount))
Log('- empty folders deleted: ' + str(emptyFoldersDeletedCount))

# Stop logging
Log('End session')
sys.exit(0)
