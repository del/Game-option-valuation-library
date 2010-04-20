#!/usr/bin/env python
# encoding: utf-8
"""
storage.py

Created by Daniel Eliasson on 2009-04-28.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import os
import demjson
from datetime import datetime
import csv


def json_to_file(dict, filepath):
	"""
	Stores a Python dictionary object as JSON in a file.
	
	@type	dict:		C{dict}
	@param	dict:		the dictionary,
	@type	filepath:	string
	@param	filepath:	the path where the file will be saved.
	
	@return:	nothing
	"""
	fh = open(filepath, 'w')
	fh.write(demjson.encode(dict, compactly=False))
	fh.close()


def json_from_file(filepath):
	"""
	Reads the JSON from a file into a Python dictionary.
	
	@type	filepath:	string
	@param	filepath:	the path where the file will be saved.
	
	@return:	a C{dict} of the JSON file
	"""
	fh = open(filepath, 'r')
	json = demjson.decode(fh.read())
	fh.close()
	return json


def csv_to_file(dict, csv_file, headers=False):
	"""
	Saves a Python dictionary as CSV in a file.
	
	@type	dict:		C{dict}
	@param	dict:		the dictionary,
	@type	csv_file:	string
	@param	csv_file:	the path where the CSV file will be saved,
	@type	headers:	boolean
	@param	headers:	whether or not to start a new CSV file and write
						the keys of the dictionary as headers in it.
	
	@return:	nothing
	
	@note: If the headers parameter is true, the file will be truncated, and
	the dictionary keys will be written on the first row, as headers for
	the CSV, with the values on the second row.
	@note: If the headers parameter is false, the values of the dictionary will
	be appended on a new row at the end of the file.
	@note: The dictionary will be written according to the sorted list of keys,
	to ensure that several dictionaries with the same keys can be written
	without scrambling of values.
	@note: This function does not verify that the dictionary being
	written is a fit for previously written values in the file.
	"""
	keys = dict.keys()
	keys.sort()
	if headers:
		w = csv.writer(open(csv_file, "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		w.writerow(keys)
	else:
		w = csv.writer(open(csv_file, "a"), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	w.writerow([dict[key] for key in keys])


def clean_valuation(valuation):
	"""
	Removes the stuff that typically gets left in the
	valuation dictionary, but shouldn't be saved to disk:
		- The S, X, and Y arrays.
	
	@type	valuation:	C{dict}
	@param	valuation:	a valuation output.
	
	@return:	the cleaned input C{dict}
	"""
	if "S" in valuation:
		del valuation["S"]
	if "X" in valuation:
		del valuation["X"]
	if "Y" in valuation:
		del valuation["Y"]
	return valuation


def save_valuation_csv(valuation, csv_file=None, headers=False):
	"""
	Saves a valuation dictionary to a CSV file, creating a new file
	based on the current date and time if C{csv_file} is C{None}.
	
	@type	valuation:	C{dict}
	@param	valuation:	the dictionary,
	@type	csv_file:	string
	@param	csv_file:	the path where the CSV file will be saved,
	@type	headers:	boolean
	@param	headers:	whether or not to start a new CSV file and write
						the keys of the dictionary as headers in it.
	
	@return: the name of the CSV file.
	"""
	valuation = clean_valuation(valuation)
	if csv_file is None:
		csv_file = os.path.join("batch_", str(datetime.now()).replace(":", "_").replace(" ", "_"), ".csv")
		headers = True
		
	csv_to_file(valuation, csv_file, headers)
	return csv_file


def save_valuation_json(valuation, batch_dir=None):
	"""
	Saves a valuation dictionary to a JSON file in C{batch_dir},
	creating a new directory based on the current date and time
	if C{batch_dir} is C{None}.
	
	@type	valuation:	C{dict}
	@param	valuation:	the dictionary,
	@type	batch_dir:	string
	@param	batch_dir:	the directory path where the JSON file will be saved.
	
	@return: a tuple containing the name of the batch directory, and the JSON file name.
	"""
	if batch_dir is None:
		batch_dir = os.path.join("batch_", str(datetime.now()).replace(":", "_").replace(" ", "_"))
	valuation_file = str(datetime.now()).replace(":", "_").replace(" ", "_") + ".json"
	
	if not os.path.exists(batch_dir):
		os.makedirs(batch_dir)
	
	valuation = clean_valuation(valuation)
	json_to_file(valuation, os.path.join(batch_dir, valuation_file))
	return batch_dir, valuation_file


def json_batch_to_csv(batch_dir, csv_file):
	"""
	Reads a batch directory of JSON files and converts
	them into a single CSV file.
	
	@type	batch_dir:	string
	@param	batch_dir:	the directory path where the JSON files are saved,
	@type	csv_file:	string
	@param	csv_file:	the path where the CSV file will be saved.
	
	@return:	nothing
	"""
	batch_data = get_batch_data(batch_dir)
	headers = True
	for valuation in batch_data:
		save_valuation_csv(valuation, csv_file, headers)
		if headers:
			headers = False


def get_batch_data(batch_dir):
	"""
	Returns an iterator over the JSON files in batch_dir.
	The JSON files will be read into a dictionary object
	and handed off to the caller.
	
	@type	batch_dir:	string
	@param	batch_dir:	the directory path where the JSON files are saved,
	
	@return:	an iterator over the JSON C{dict}s
	"""
	batch_data = []
	files = os.listdir(batch_dir)
	for valuation_file in files:
		yield json_from_file(os.path.join(batch_dir, valuation_file))


def ensure_dir_exists(directory):
	"""
	Checks if the specified directory exists, and if not, creates it.
	
	@type	directory:	string
	@param	directory:	the directory path that should exist.
	
	@return:	nothing
	"""
	if not os.path.exists(directory):
		os.makedirs(directory)


def rand_gen_state_to_json(rand_gen_state):
	"""
	Converts a NumPy random number generator state object into
	a Python dictionary, so that it can be saved in the JSON format.
	
	@param	rand_gen_state:	NumPy random number generator state object.
	
	@return: a dictionary containing the information from the input
	"""
	return {
		"mt19937": rand_gen_state[0],
		"int_keys": rand_gen_state[1].tolist(),
		"pos": rand_gen_state[2],
		"has_gauss": rand_gen_state[3],
		"cached_gaussian": rand_gen_state[4]
	}


def json_to_rand_gen_state(json):
	"""
	Creates a Numpy random number generator state object
	from a Python dictionary.
	
	@type	json:	C{dict}
	@param	json:	A random number generator state dictionary, as created by L{gcc.storage.rand_gen_state_to_json}.
	
	@return:	a NumPy random number generator state object
	"""
	return (json["mt19937"], np.array(json["int_keys"], dtype=uint32), json["pos"], json["has_gauss"], json["cached_gaussian"])