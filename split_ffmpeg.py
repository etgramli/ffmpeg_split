#!/usr/bin/env python
import os
import re
import pprint
import sys
import subprocess as sp
from os.path import basename
from subprocess import *
from optparse import OptionParser

def parseChapters(filename):
  chapters = []
  command = [ "ffprobe", '-i', filename]
  output = ""

  try:
    # Use ffprobe instead of ffmpeg since the latter one throws an error if no output file is specified.
    output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
  except CalledProcessError(e):
    output = e.output

  num = 1
  chapter_match = None
  title = None
  for line in iter(output.splitlines()):
    current_title_match = re.match(r".*title.*: (.*)", line)

    if current_title_match == None:
      title = None
      current_chapter_match = re.match(r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*", line)
      if current_chapter_match != None:
        chapter_match = current_chapter_match
    else:
      title = current_title_match.group(1)

    if title != None and chapter_match != None:
      chapters.append({ "name": repr(num) + " - " + title, "start": chapter_match.group(2), "end": chapter_match.group(3)})
      num += 1
      chapter_match = None
      title = None

  return chapters

def getChapters(infile):
  chapters = parseChapters(infile)
  fbase, fext = os.path.splitext(infile)
  path, file = os.path.split(infile)
  newdir, fext = os.path.splitext( basename(infile) )

  out_path = path + "/" + newdir
  if not path:
	  out_path = newdir
  os.mkdir(out_path)

  for chap in chapters:
    chap['name'] = chap['name'].replace('/',':')
    chap['name'] = chap['name'].replace("'","\'")
    print("start:" +  chap['start'])
    chap['outfile'] = out_path + "/" + re.sub("[^-a-zA-Z0-9_.():' ]+", '', chap['name']) + fext
    chap['origfile'] = infile
    print(chap['outfile'])
  return chapters

def convertChapters(chapters):
  for chap in chapters:
    print("start:" +  chap['start'])
    print(chap)
    command = [
        "ffmpeg", '-i', chap['origfile'],
        '-vcodec', 'copy',
        '-acodec', 'copy',
        '-ss', chap['start'],
        '-to', chap['end'],
        chap['outfile']]
    output = ""
    try:
      # ffmpeg requires an output file and so it errors
      # when it does not get one
      output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
    except CalledProcessError(e):
      output = e.output
      raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

def convertChaptersToFlac(chapters, audioIndex=0): # By default use first audio track
  for chap in chapters:
    chap['outfile'] = os.path.splitext(chap['outfile'])[0] + '.flac'
    print("start:" +  chap['start'])
    print(chap)
    command = [
        "ffmpeg", '-i', chap['origfile'],
        '-vn', # No video output
        '-c:a', 'flac',
        '-map', '0:a:' + audioIndex,
        '-ss', chap['start'],
        '-to', chap['end'],
        chap['outfile']]
    output = ""
    try:
      # ffmpeg requires an output file and so it errors when it does not get one
      output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
    except CalledProcessError(e):
      output = e.output
      raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

def main():
  parser = OptionParser(usage="usage: %prog -i filename", version="%prog 1.0")
  parser.add_option("-i", "--input", dest="infile", help="Input File", metavar="FILE")
  parser.add_option("-a", "--audioStream", dest="audioIndex", help="Audio stream index")
  (options, args) = parser.parse_args()
  if not options.infile:
    parser.error('Input file ("-i") required')
  chapters = getChapters(options.infile)
  if not options.audioIndex:
    convertChapters(chapters)
  else:
    convertChaptersToFlac(chapters, options.audioIndex)

if __name__ == '__main__':
  main()
