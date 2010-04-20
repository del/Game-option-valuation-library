#!/usr/bin/env python
# encoding: utf-8
"""
json_batch_to_csv.py

Created by Daniel Eliasson on 2009-09-09.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import sys
import getopt
sys.path.append('..')
import gcc.storage


help_message = '''
Usage:
python json_batch_to_csv.py -b/--batch-dir batch_dir -c/--csv-file cvs_file

-b/--batch-dir	directory with batch JSON output in it

-c/--csv-file	CSV file to output to
'''


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "b:c:", ["batch-dir=", "csv-file="])
		except getopt.error, msg:
			raise Usage(msg)
		
		# option processing
		batch_dir = None
		csv_file = None
		for option, value in opts:
			if option in ("-b", "--batch-dir"):
				batch_dir = value.strip()
			if option in ("-c", "--csv-file"):
				csv_file = value.strip()
		if batch_dir is None or csv_file is None:
			raise Usage(help_message)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2
		
	gcc.storage.json_batch_to_csv(batch_dir, csv_file)


if __name__ == "__main__":
	sys.exit(main())
