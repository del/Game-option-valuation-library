#!/usr/bin/env python
# encoding: utf-8
"""
convertible_bond_example.py

Created by Daniel Eliasson on 2009-09-09.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import sys
import getopt
sys.path.append('..')
import gcc.storage
import gcc.security_simulation
import gcc.claims.convertible_bond


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


help_message = '''
Usage:
python convertible_bond_example.py -b/--batch-dir batch_dir_name [-n/--no-lse]

-b/--batch-dir	the directory where the output will be saved

-n/--no-lse		use the LSE-free version of the algorithm
'''


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "b:hn",
				["batch-dir=", "help", "no-lse"])
		except getopt.error, msg:
			raise Usage(msg)
			
		# option processing
		batch_dir = None
		no_lse = False
		for option, value in opts:
			if option in ("-h", "--help"):
				raise Usage(help_message)
			if option in ("-b", "--batch-dir"):
				batch_dir = value.strip()
			if option in ("-n", "--no-lse"):
				no_lse = True
		if batch_dir is None:
			raise Usage(help_message)
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2
		
	if no_lse:
		m_tuple = (None,)
	else:
		m_tuple = (8, 16,)
		
	# Risk-free interest rate and parameters of the underlying
	r = 0.06
	volatility = 0.4
	d = 0.02
	eta = 10
	theta = 7
	
	# Convertible bond parameters
	K = 1.3
	gamma = 0.9
	T = 0.5
	
	for N in (1000, 2000,):
		for L in (101, 201,):
			for m in m_tuple:
				for S0 in (0.8, 1.0, 1.2, 1.3, 1.4):
					print "N =", N, "  L =", L, "  m =", m
					print "K =", K, "  gamma =", gamma, "  T =", T, "  r = ", r
					print "d =", d, "  volatility = ", volatility, "  eta =", eta, "  theta =", theta
					
					# Generate the stock paths using jump-diffusion model
					S, rand_gen_state = gcc.security_simulation.jump_diffusion(S0=S0, r=r, volatility=volatility, d=d, eta=eta, theta=theta, T=T, N=N, L=L)
					
					# Build parameter dictionary
					params = {
						"S0": S0, "S": S, "r": r, "volatility": volatility, "d": d, "eta": eta, "theta": theta,
						"T": T, "N": N, "L": L, "K": K, "gamma": gamma
					}
					
					# Value the convertible bond
					if not no_lse:
						params.update({"m": m})
					valuation = gcc.claims.convertible_bond.value(**params)
					
					print "Option price: V =", valuation["V"], "  Var =", valuation["var"], "  dev =", valuation["dev"], "calculated in", valuation["time"], "\n\n"
					batch_dir, valuation_file = gcc.storage.save_valuation_json(valuation, batch_dir)
	print "Valuations saved in ", batch_dir


if __name__ == "__main__":
	sys.exit(main())
