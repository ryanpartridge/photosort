#!/usr/bin/python3

import sys
from argparse import ArgumentParser
import os

class PhotoSorter3:
    exivTimestampTags = ['Exif.Photo.DateTimeOriginal',
                         'Exif.Photo.DateTimeDigitized',
                         'Exif.Image.DateTime']

def main():
    parser = ArgumentParser()
    parser.add_argument("-n", "--no-action", action="store_true", help="Just show what would happen -- don't actually do anything")
    parser.add_argument("-i", "--input-directory", dest="in_dir", required=True, help="Directory to serach for jpeg files")
    parser.add_argument("-o", "--output-directory", dest="out_dir", required=True, help="Directory where sorted jpeg files will be copied")
    parser.add_argument("-r", "--recurse", action="store_true", help="Recursively search the input directory for picture files")
    parser.add_argument("-d", "--delete-original", action="store_true", help="Recursively search the input directory for picture files")
    args = parser.parse_args()

    if not os.path.isdir(args.in_dir):
        print("Must specify a valid input directory", file=sys.stderr)
        return 1

    if not os.path.exists(args.out_dir):
        print("Creating output directory " + args.out_dir)
    elif not os.path.isdir(args.out_dir):
        print("Output path exists, but is not a directory", file=sys.stderr)
        return 1

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit as e:
        sys.exit(e)
    except BaseException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
