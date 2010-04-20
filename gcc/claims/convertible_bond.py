#!/usr/bin/env python
# encoding: utf-8
"""
convertible_bond.py

Created by Daniel Eliasson on 2009-09-09.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

from .. import valuation
import numpy as np

def value(S, K, gamma, r, T, **params):
	"""
	Values a convertible bond.
	
	@type	S:		(L+1) x N-array
	@param	S:		the simulated underlying paths. L is the number of time steps - 1
					(timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
	@type	K:		number
	@param	K:		the recall price,
	@type	gamma:	number
	@param	gamma:	the amount of stock the bond can be converted into,
	@type	r:		number
	@param	r:		the risk-free interest rate,
	@type	T:		number
	@param	T:		the maturity time, measured in years,
	@type	params:	C{dict}
	@param	params:	optional parameters to pass on to the output.
	
	@return:		the output of L{gcc.valuation.value_gcc}
	"""
	params.update({"S": S, "K": K, "gamma": gamma, "r": r, "T": T})
	L = S.shape[0] - 1
	
	Y = gamma*S
	X = np.maximum(gamma*S, K)
	Y[L, :] = np.maximum(gamma*S[L, :], 1)
	X[L, :] = Y[L, :]
	return valuation.value_gcc(X=X, Y=Y, **params)