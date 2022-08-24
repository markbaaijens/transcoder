#!/usr/bin/python3
#
# Authors.: Mark Baaijens, Mike van Dartel, Debora Kniknie
#

import time
import os
import subprocess
from fnmatch import fnmatch
import sys

flacsScannedCount = 0
mp3TranscodedCount = 0
oggTranscodedCount = 0
coverFilesCopiedCount = 0
coverEmbeddedCount = 0
obsoleteFilesDeletedCount = 0
emptyFoldersDeletedCount = 0

constMp3 = 'mp3'
constOgg = 'ogg'
constLogFileName = 'transcoder.log'

sourceTree = ''
oggTree = ''
oggQuality = 1
oggEncoding = 0
mp3Tree = ''
mp3Bitrate = 128
mp3Encoding = 0
dryRun = 0
logDir = ''
showVerbose = 0

def LogFileName():
    logFileName = ''
    if (logDir != ''):
        logFileName = os.path.join(logDir,  constLogFileName)
    return logFileName

def Log(logText, keepRawDir=False, forceConsole=False):
    if dryRun:
        logText = '(dry-run) ' + logText

    if not keepRawDir:
        if (oggTree != '') and (oggTree in logText):
            logText = logText.replace(oggTree, '[ogg_tree]')

        if (mp3Tree != '') and (mp3Tree in logText):
            logText = logText.replace(mp3Tree, '[mp3_tree]')

        # Hence: this replacement must be last to prevent double replacements
        if (sourceTree != '') and (sourceTree in logText):
            logText = logText.replace(sourceTree, '[source_tree]')

    if (LogFileName() != ''):
        outputFile = open(LogFileName(), 'a')
        outputFile.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + logText + '\n' )
        outputFile.close()

    if (showVerbose or forceConsole):
        print(logText)
      
    return

def TransCodeFile(inputFile, outputFile, transcodeFormat): 
    Log('- transcoding file: "' + inputFile + '" to ' + transcodeFormat)

    if not dryRun:
        outputFilebasedir = os.path.split(outputFile)[0]
        if not os.path.exists(outputFilebasedir):
            os.makedirs(outputFilebasedir)

        if transcodeFormat == constOgg:  
            TransCodeFileOgg(inputFile, outputFile)    

        if transcodeFormat == constMp3:
            TransCodeFileMp3(inputFile, outputFile)

        if os.path.exists(outputFilebasedir + "/cover.jpg"):
            os.remove(outputFilebasedir + "/cover.jpg")
      
    return
    
def TransCodeFileOgg(inputFile, outputFile): 
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    # Determine name of a *local* temporary ogg-file; this makes it easier for
    # rights management (Popen is suspect to be critical about this)
    tempOggFile = tempfile.gettempdir() + '/' + 'temp.ogg'  

    # Important: Q = quiet option is imperative for running this script through a scheduler (cron); 
    # not using this option results in unpredictable behaviour!
    p = subprocess.Popen(["nice", "oggenc", inputFile, "-Q", "-q" + str(oggQuality), "-o" + tempOggFile], stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
        Log('- an error occured during transcoding')
        Log('=>' + output) 

    copyfile(tempOggFile, outputFile) 

    os.remove(tempOggFile)

    global oggTranscodedCount
    oggTranscodedCount +=1

    return
    
def TransCodeFileMp3(inputFile, outputFile): 
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    # Determine name of a *local* temporary wav-file; this makes it easier for
    # rights management (Popen is suspect to be critical about this)
    tempWavFile = tempfile.gettempdir() + '/' + 'temp.wav'

    # Important: -s silent option is imperative for running this script through a scheduler (cron); 
    # not using this option results in unpredictable behaviour!
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
      
    # Important: --silent option is imperative for running this script through a scheduler (cron); 
    # not using this option results in unpredictable behaviour!    
    # -f = fast mode
    # Tagging can only be done if the mp3 file has a valid id3 header. We can force this by adding 
    # a dummy tt argument (--tt dummy) during encoding.     
    p = subprocess.Popen(["nice", "lame", "-f", "--silent", "--noreplaygain", "--id3v2-only", "-b" + str(mp3Bitrate), "--tt",  "dummy", tempWavFile, tempMP3File], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[1]
    if p.returncode != 0:
        Log('- an error occured during transcoding')
        Log('=>' + output) 
 
    CopyTagsToTranscodedFileMp3(inputFile, tempMP3File)

    copyfile(tempMP3File, outputFile) 

    os.remove(tempWavFile)
    os.remove(tempMP3File)
      
    global mp3TranscodedCount
    mp3TranscodedCount += 1
 
    return

def CopyTagsToTranscodedFileMp3(losslessFile, lossyFile):  
    # Because the input flac file is decoded to wav, all metadata is lost. We have to extract this metadata from 
    # the flac file and put it directly into the generated mp3 file.
    from mutagen.flac import FLAC
    from mutagen.id3 import ID3   
    
    flacFile = FLAC(losslessFile)
    flacFileTags = flacFile.tags 
          
    mp3File = ID3(lossyFile)    
    mp3File.delete()    
        
    for key,value in flacFileTags.items():
        if key == 'title': 
            from mutagen.id3 import TIT2
            mp3File.add(TIT2(encoding=3, text=value)) 
        elif key == 'album': 
            from mutagen.id3 import TALB
            mp3File.add(TALB(encoding=3, text=value))
        elif key == 'artist': 
            from mutagen.id3 import TPE1
            mp3File.add(TPE1(encoding=3, text=value)) 
        elif key == 'tracknumber': 
            from mutagen.id3 import TRCK
            mp3File.add(TRCK(encoding=3, text=value))
        elif key == 'date': 
            from mutagen.id3 import TDRC
            mp3File.add(TDRC(encoding=3, text=value))
        elif key == 'genre': 
            from mutagen.id3 import TCON
            mp3File.add(TCON(encoding=3, text=value))
        elif key == 'discnumber': 
            from mutagen.id3 import TPOS
            mp3File.add(TPOS(encoding=3, text=value))
        elif key == 'composer': 
            from mutagen.id3 import TCOM
            mp3File.add(TCOM(encoding=3, text=value))
        elif key == 'conductor': 
            from mutagen.id3 import TPE3
            mp3File.add(TPE3(encoding=3, text=value))
        elif key == 'ensemble': 
            from mutagen.id3 import TPE2
            mp3File.add(TPE2(encoding=3, text=value))      
        elif key == 'comment': 
            from mutagen.id3 import COMM
            mp3File.add(COMM(encoding=3, text=value))
        elif key == 'publisher': 
            from mutagen.id3 import TPUB
            mp3File.add(TPUB(encoding=3, text=value))
        elif key == 'opus': 
            from mutagen.id3 import TIT3
            mp3File.add(TIT3(encoding=3, text=value))
        elif key == 'sourcemedia': 
            from mutagen.id3 import TMED
            mp3File.add(TMED(encoding=3, text=value))
        elif key == 'isrc': 
            from mutagen.id3 import TSRC
            mp3File.add(TSRC(encoding=3, text=value))
        elif key == 'license': 
            from mutagen.id3 import TOWN
            mp3File.add(TOWN(encoding=3, text=value))
        elif key == 'copyright': 
            from mutagen.id3 import WCOP
            mp3File.add(WCOP(encoding=3, text=value))
        elif key == 'encoded-by': 
            from mutagen.id3 import TENC
            mp3File.add(TENC(encoding=3, text=value))
        elif (key == 'part' or key == 'partnumber'): 
            from mutagen.id3 import TIT3
            mp3File.add(TIT3(encoding=3, text=value))
        elif (key == 'lyricist' or key == 'textwriter'): 
            from mutagen.id3 import TIT3
            mp3File.add(TIT3(encoding=3, text=value))
        else: 
            from mutagen.id3 import TXXX
            mp3File.add(TXXX(encoding=3, text=value, desc=key))        
      
        mp3File.update_to_v24()
        mp3File.save() 
      
    return

def CleanUpLossyTree(lossyTree, lossyFormat):
    Log('Cleanup ' + lossyTree) 
    global obsoleteFilesDeletedCount 

    for dir, dirNames, fileNames in os.walk(lossyTree, topdown=False): # Note the topdown: we must cleanup beginning from the deepest folder
        dirNames.sort()

        for fileName in sorted(fileNames):
            if fnmatch(fileName, '*.' + lossyFormat): 
                lossyFile = os.path.join(dir, fileName) 
                
                sourcePath = dir.replace(lossyTree, sourceTree)        
                sourceFile = os.path.join(sourcePath, fileName)        
                sourceFile = os.path.splitext(sourceFile)[0] + '.flac' 

                if not os.path.isfile(sourceFile):                              
                    if not dryRun:
                        os.remove(lossyFile)
                    Log('- file deleted: ' + lossyFile)
                    obsoleteFilesDeletedCount  += 1
            else: 
                if fnmatch(fileName, '*.*'): 
                    lossyFile = os.path.join(dir, fileName) 
                    
                    sourcePath = dir.replace(lossyTree, sourceTree)        
                    sourceFile = os.path.join(sourcePath, fileName)        

                    if not os.path.isfile(sourceFile):                              
                        if not dryRun:
                            os.remove(lossyFile)
                        Log('- file deleted: ' + lossyFile)
                        obsoleteFilesDeletedCount  += 1

    RemoveEmptyDirectories(lossyTree)
    RemoveEmptyDirectories(lossyTree) # Do it twice to also remove empty parent directories

    return

def RemoveEmptyDirectories(tree):
  for dir, dirNames, fileNames in os.walk(tree, topdown=False): # Note the topdown: we must cleanup beginning from the deepest folder
      dirNames.sort()
      
      if (len(dirNames) == 0) and (len(fileNames) == 0) and (dir != tree): # Never remove the top dir!   
          if not dryRun:
              os.rmdir(dir)
          Log('- directory removed: ' + dir) 
          global emptyFoldersDeletedCount
          emptyFoldersDeletedCount +=1

  return

def TransCodeFiles():
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

                if oggEncoding == 1:    
                    outputFile = os.path.splitext(sourceFileFullPathName)[0] + '.' + constOgg  
                    outputFile = outputFile.replace(sourceTree, oggTree)        
                  
                    if (not os.path.exists(outputFile)) or (os.path.getmtime(sourceFileFullPathName) > os.path.getmtime(outputFile)):
                        TransCodeFile(sourceFileFullPathName, outputFile, constOgg)

                if mp3Encoding == 1:    
                    outputFile = os.path.splitext(sourceFileFullPathName)[0] + '.' + constMp3  
                    outputFile = outputFile.replace(sourceTree, mp3Tree)         

                    if (not os.path.exists(outputFile)) or (os.path.getmtime(sourceFileFullPathName) > os.path.getmtime(outputFile)):
                        TransCodeFile(sourceFileFullPathName, outputFile, constMp3)      

    return

def EmbedAlbumArt(lossyTree):
    from shutil import copyfile # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
    from math import trunc 
    
    Log('Embed album art files to lossy tree: ' + lossyTree)
    for dir, dirNames, fileNames in os.walk(sourceTree):
        dirNames.sort()

        for fileName in sorted(fileNames):
            sourceFullFileName = os.path.join(dir, fileName)
            if fnmatch(sourceFullFileName, "*/cover.jpg"):
                sourceCoverFullFileName = sourceFullFileName
                lossyCoverFullFileName = sourceCoverFullFileName.replace(sourceTree, lossyTree)  

                if (not os.path.isfile(lossyCoverFullFileName)) or (os.path.getmtime(sourceCoverFullFileName) > os.path.getmtime(lossyCoverFullFileName)):
                    Log('- copying album art to ' + lossyCoverFullFileName) 
                    global coverFilesCopiedCount
                    coverFilesCopiedCount += 1

                    if not dryRun:
                        # Create intermediate-level directories in the output tree; normally, these already exist
                        # because during transcoding they will be created; but this is 'just in case'
                        lossyCoverBaseDir = os.path.split(lossyCoverFullFileName)[0]
                        if not os.path.exists(lossyCoverBaseDir):
                            os.makedirs(lossyCoverBaseDir)       

                        copyfile(sourceCoverFullFileName, lossyCoverFullFileName) 

                        global coverEmbeddedCount
                        for fileName in sorted(os.listdir(lossyCoverBaseDir)):
                            lossyFileFullFileName = os.path.join(lossyCoverBaseDir,  fileName)  
                            if os.path.splitext(fileName)[1] ==  '.' + constMp3:
                                UpdateCoverMp3(lossyFileFullFileName, lossyCoverFullFileName)
                                coverEmbeddedCount += 1
                            if os.path.splitext(fileName)[1] == '.' + constOgg:
                                UpdateCoverOgg(lossyFileFullFileName, lossyCoverFullFileName)                    
                                coverEmbeddedCount += 1

    return  

def UpdateCoverMp3(lossyFileName, artworkFileName):   
    from mutagen.id3 import ID3, APIC
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)

    Log('- embedding album art in ' + lossyFileName) 

    # Copy lossy file to a local location; to prevent (save) errors in a samba environment
    tempLossyFile = tempfile.gettempdir() + '/' + 'temp.mp3'
    copyfile(lossyFileName, tempLossyFile) 

    audio = ID3(tempLossyFile)
    with open(artworkFileName, 'rb') as albumart:
        audio['APIC'] = APIC(
                      encoding=3,
                      mime='image/jpeg',
                      type=3, desc=u'cover',
                      data=albumart.read())
    audio.save()

    copyfile(tempLossyFile, lossyFileName) 
    os.remove(tempLossyFile)  

    return

def UpdateCoverOgg(lossyFileName, artworkFileName):   
    import base64; from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import Picture; import PIL.Image
    import tempfile
    from shutil import copyfile  # Use copyfile b/c this will *not* copy rights (which is error prone on gvfs/samba)
    
    Log('- embedding album art in ' + lossyFileName) 

    # Copy lossy file to a local location; to prevent (save) errors in a samba environment
    tempLossyFile = tempfile.gettempdir() + '/' + 'temp.ogg'
    copyfile(lossyFileName, tempLossyFile) 

    o = OggVorbis(tempLossyFile)

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

    copyfile(tempLossyFile, lossyFileName) 
    os.remove(tempLossyFile)  
    
    return

def StripLastSlashFromPathName(fileName):
    if (fileName[-1:] in ['/', '\\']):
        fileName = fileName[:-1] 
    return fileName

def Main():
    global sourceTree
    global oggTree
    global oggQuality
    global oggEncoding
    global mp3Tree
    global mp3Bitrate
    global mp3Encoding
    global dryRun
    global logDir
    global showVerbose

    import argparse
    parser = argparse.ArgumentParser(description='Transcode lossless audio files (flac) to lossy formats (mp3/ogg).')

    parser.add_argument('--sourcefolder', metavar='sourcefolder', type=str, help='folder containing source files (flac)', nargs=1)
    parser.add_argument('-v', '--verbose', help="increase output verbosity; show (more) output to console", action="store_true")
    parser.add_argument('-d', '--dry-run', help="perform a trial run with no changes made",  action="store_true")        
    parser.add_argument('--logfolder', type=str, help="folder where log (= transcoder.log) is stored; no folder is no logging",  nargs=1) 
    parser.add_argument('--mp3folder', type=str, help="folder where transcoded mp3's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
    parser.add_argument('--mp3bitrate', type=int, help="quality of the transcoded ogg files; default is 128",  nargs=1,  choices=[128, 256, 384]) 
    parser.add_argument('--oggfolder', type=str, help="folder where transcoded ogg's are stored; no folder is no transcoding, folder must exist",  nargs=1) 
    parser.add_argument('--oggquality', type=int, help="quality of the transcoded ogg files; default is 1",  nargs=1,  choices=[1, 2, 3, 4, 5]) 

    args = parser.parse_args()    

    if args.verbose:
        showVerbose = args.verbose
    if args.dry_run:        
        dryRun = args.dry_run

    if (args.sourcefolder != None) and (args.sourcefolder[0] != ''):
        sourceTree = args.sourcefolder[0]
    sourceTree = StripLastSlashFromPathName(sourceTree)

    if (args.logfolder != None) and (args.logfolder[0] != ''):
        logDir = args.logfolder[0]
    logDir = StripLastSlashFromPathName(logDir)   

    if (args.mp3folder != None) and (args.mp3folder[0] != ''):
        mp3Tree = args.mp3folder[0]
    mp3Tree = StripLastSlashFromPathName(mp3Tree)

    if (args.oggfolder != None) and (args.oggfolder[0] != ''):
        oggTree = args.oggfolder[0]
    oggTree = StripLastSlashFromPathName(oggTree)
            
    if (args.oggquality != None) and (args.oggquality[0] != ''):
        oggQuality = args.oggquality[0]

    if (args.mp3bitrate != None) and (args.mp3bitrate[0] != ''):
        mp3Bitrate = args.mp3bitrate[0]

    oggEncoding = (oggTree != '')
    mp3Encoding = (mp3Tree != '')

    if (logDir != '') and (not os.path.exists(logDir)):
        print('Location of logfolder = ' + logDir + ' is not valid. Abort.')
        sys.exit(1)

    if (sourceTree == ''):
        Log('Value of sourcefolder is required. Abort.', True, True)
        sys.exit(1)        

    if (sourceTree != '') and (not os.path.exists(sourceTree)):
        Log('Location of sourcefolder = ' + sourceTree + ' is not valid. Abort.', True, True)
        sys.exit(1)

    if (oggEncoding == 1) and (not os.path.exists(oggTree)):
        Log('Location of oggfolder = ' + oggTree + ' is not valid. Abort.', True, True)
        sys.exit(1)

    if (mp3Encoding == 1) and (not os.path.exists(mp3Tree)):
        Log('Location of mp3folder = ' + mp3Tree + ' is not valid. Abort.', True, True)
        sys.exit(1)

    lockfile = '/tmp/transcoder.lock'
    if os.path.exists(lockfile):
        Log('Starting transcoder. But another process is still running, lockfile found ("rm ' + lockfile + '" to continue). Abort.', True, True)
        sys.exit(1)

    # Remove lockfile on exit, even when the user hits Crtl+C
    import atexit
    atexit.register(os.remove, lockfile)

    outputFile = open(lockfile,'w')
    outputFile.write('lock')
    outputFile.close()

    if (logDir == '') and (not showVerbose):
        print('Hint: to monitor progress, use --verbose or --logfolder (or both)')

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

    TransCodeFiles()
          
    if oggEncoding:
        EmbedAlbumArt(oggTree)
    if mp3Encoding:
        EmbedAlbumArt(mp3Tree)

    if oggEncoding:
        CleanUpLossyTree(oggTree, constOgg)
    if mp3Encoding:
        CleanUpLossyTree(mp3Tree, constMp3)

    Log('Summary')
    Log('- flacs scanned: ' + str(flacsScannedCount))
    Log('- transcoded to mp3: ' + str(mp3TranscodedCount))
    Log('- transcoded to ogg: ' + str(oggTranscodedCount))
    Log('- cover files copied: ' + str(coverFilesCopiedCount))
    Log('- covers embedded in files: ' + str(coverEmbeddedCount))
    Log('- obsolete files deleted: ' + str(obsoleteFilesDeletedCount))
    Log('- empty folders deleted: ' + str(emptyFoldersDeletedCount))

    Log('End session')
    sys.exit(0)

    return

if __name__ == '__main__':
    Main()
