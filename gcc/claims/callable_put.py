#!/usr/bin/env python
# encoding: utf-8
"""
callable_put.py

Created by Daniel Eliasson on 2009-09-09.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

from .. import valuation
import numpy as np

def value(S, K, delta, r, T, **params):
	"""
	Values a callable put option.
	
	@type	S:		(L+1) x N-array
	@param	S:		the simulated underlying paths. L is the number of time steps - 1
					(timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
	@type	K:		number
	@param	K:		the strike of the put component,
	@type	delta:	number
	@param	delta:	the penalty for calling the option,
	@type	r:		number
	@param	r:		the risk-free interest rate,
	@type	T:		number
	@param	T:		the maturity time, measured in years,
	@type	params:	C{dict}
	@param	params:	optional parameters to pass on to the output.
	
	@return:		the output of L{gcc.valuation.value_gcc}
	"""
	params.update({"S": S, "K": K, "delta": delta, "r": r, "T": T})
	
	X = np.maximum(K - S, 0) + delta
	Y = np.maximum(K - S, 0)
	L = X.shape[0] - 1
	X[L, :] = Y[L, :]
	return valuation.value_gcc(X=X, Y=Y, **params)