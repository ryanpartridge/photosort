'''
Created on Apr 1, 2012

@author: ryan
'''
import sys
import os
import pyexiv2
import shutil
import datetime
from optparse import OptionParser

class PhotoSorter:
    exivTimestampTags = ['Exif.Photo.DateTimeOriginal',
                         'Exif.Photo.DateTimeDigitized',
                         'Exif.Image.DateTime']

    UNKNOWN = "unknown"

    def __init__(self, in_dir, out_dir, recurse=False, delete_original=False, dry_run=False):
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.recurse = recurse
        self.delete_original = delete_original
        self.dry_run = dry_run
        self.file_count_map = {}
        self.unknown_file_count = -1
        self.primary_cache_hit = 0
        self.primary_cache_miss = 0
        self.secondary_cache_hit = 0
        self.secondary_cache_miss = 0

    def setup(self):
        if not os.path.exists(self.out_dir):
            if not self.dry_run:
                print "Creating output directory " + self.out_dir
                os.makedirs(self.out_dir)
        elif not os.path.isdir(self.out_dir):
            print >> sys.stderr, "Output path exists, but it not a directory"
            exit(1)

    def process(self):
        self.setup()
        self.processDir(os.path.abspath(self.in_dir))
        self.printReport()

    def processDir(self, dirPath):
        files = os.listdir(dirPath)
        files.sort()
        for f in files:
            if not f.startswith("."):
                fpath = os.path.abspath(dirPath + os.sep + f)
                if os.path.isdir(fpath) and self.recurse:
                    if self.recurse:
                        self.processDir(fpath)
                else:
                    self.processFile(fpath)

    def processFile(self, filePath):
        (root, ext) = os.path.splitext(filePath)
        if ext.lower() in [".jpg", ".jpeg"]:
            print "Original filename: " + filePath
            timestamp = self.getTimestamp(filePath)
            if timestamp:
                print "Image date: " + str(timestamp)
                filePrefix = timestamp.strftime("%Y_%m_%d")
                (year, month, day) = filePrefix.split('_')
                parentDir = os.path.abspath(self.out_dir + os.sep + year + os.sep + month)
            else:
                print "Image date unknown"
                filePrefix = PhotoSorter.UNKNOWN
                parentDir = os.path.abspath(self.out_dir + os.sep + PhotoSorter.UNKNOWN)

            fileCount = self.getFilecount(parentDir, filePrefix)
            newpath = "{:s}{:s}{:s}-{:03d}.jpg".format(parentDir, os.sep, filePrefix, fileCount)
            print "New path: " + newpath
            if not self.dry_run:
                if not self.dry_run:
                    self.copyfile(filePath, newpath)
                    if self.delete_original:
                        os.remove(filePath)
        else:
            print "*** Not processing non-image file: " + filePath + " ***"

        print

    def getTimestamp(self, filePath):
        metadata = pyexiv2.ImageMetadata(filePath)
        metadata.read()
        timestamp = None
        for tag in PhotoSorter.exivTimestampTags:
            try:
                ts = metadata[tag].value
                if ts and isinstance(ts, datetime.datetime):
                    timestamp = ts
                    break
            except:
                pass
        return timestamp
    
    def getFilecount(self, parentDir, filePrefix):
        def findHighestNumber():
            highest = -1
            if not os.path.isdir(parentDir):
                if not self.dry_run:
                    os.makedirs(parentDir)
            else:
                existing = filter(lambda x: x.startswith(filePrefix + "-"), os.listdir(parentDir))
                if existing:
                    existing.sort(reverse=True)
                    highest = int(existing[0].split("-")[1].split(".")[0])
            return highest

        fileCount = 0
        if filePrefix == PhotoSorter.UNKNOWN:
            if self.unknown_file_count < 0:
                self.unknown_file_count = findHighestNumber()
            self.unknown_file_count += 1
            fileCount = self.unknown_file_count

        else:
            (year, month, day) = filePrefix.split('_')
            if parentDir in self.file_count_map:
                self.primary_cache_hit += 1
                if day not in self.file_count_map[parentDir]:
                    self.secondary_cache_miss += 1
                    self.file_count_map[parentDir][day] = findHighestNumber()
                else:
                    self.secondary_cache_hit += 1
            else:
                self.primary_cache_miss += 1
                self.file_count_map[parentDir] = {day : findHighestNumber()}
            self.file_count_map[parentDir][day] += 1
            fileCount = self.file_count_map[parentDir][day]

        return fileCount

    def copyfile(self, src, dst):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copyfile(src, dst)
        st = os.stat(src)
        if hasattr(os, 'utime'):
            os.utime(dst, (st.st_atime, st.st_mtime))

    def printReport(self):
        print
        print "-------------------------------------"
        print "Primary cache hits:", self.primary_cache_hit
        print "Primary cache misses", self.primary_cache_miss
        print "Secondary cache hits:", self.secondary_cache_hit
        print "Secondary cache misses", self.secondary_cache_miss
        print "-------------------------------------"
        print

def main():
    parser = OptionParser("usage %prog [options]")

    parser.add_option("-n", "--dry-run", action="store_true", help="Just show what would happen; don't actually do anything")
    parser.add_option("-i", "--input-directory", dest="in_dir", help="Directory to search for jpeg files")
    parser.add_option("-o", "--output-directory", dest="out_dir", help="Directory where sorted jpeg files will be copied")
    parser.add_option("-r", "--recurse", action="store_true", help="Recursively search the input directory for picture files")
    parser.add_option("-d", "--delete-original", action="store_true", help="Recursively search the input directory for picture files")

    (options, args) = parser.parse_args()
    
    # validate options
    if not options.in_dir or not os.path.isdir(options.in_dir):
        print >> sys.stderr, "Must specify a valid input directory"
        exit(1)

    if not options.out_dir:
        print >> sys.stderr, "Must specify an output directory"
        exit(1)

    if not os.path.exists(options.out_dir):
        print "Creating output directory " + options.out_dir
        os.makedirs(options.out_dir)
    elif not os.path.isdir(options.out_dir):
        print >> sys.stderr, "Output path exists, but it not a directory"
        exit(1)

    photoSorter = PhotoSorter(options.in_dir, options.out_dir, options.recurse, options.delete_original, options.dry_run)
    photoSorter.process()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except object, e:
        print >> sys.stderr, e
        sys.exit(1)