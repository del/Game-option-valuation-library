#!/usr/bin/env python
# encoding: utf-8
"""
polynomials.py

Created by Daniel Eliasson on 2009-04-30.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import numpy as np
import numpy.linalg


def get_eval_func(poly_type):
    """
    @type    poly_type:    string
    @param   poly_type:    the type of functions in the projection subspace, as recognised
                           by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.

    @return:    the polynomial evaluation function for the given type of polynomial.
    """
    if poly_type == "hermite":
        return hermite_eval_upto
    elif poly_type == "laguerre":
        return laguerre_eval_upto
    else:
        return hermite_eval_upto


def laguerre_eval_upto(x, m):
    """
    Evaluates Laguerre polynomials 0 through M{m-1} at M{x}.

    @type    x:    number
    @param   x:    the point to evaluate the polynomials,
    @type    m:    integer
    @param   m:    the number of polynomials to evaluate.

    @return:    an N-array of the evaluated polynomials.
    """
    N         = x.shape[0]
    laguerres = np.c_[np.ones((N, 1)), 1 - x, np.empty((N, m-2))]
    if m > 2:
        for i in range(2, m):
            laguerres[:, i] = (1.0/i)*(  (2*i - 1 - x) * laguerres[:, i-1]
                                       - (i-1)         * laguerres[:, i-2])
    return laguerres


def hermite_eval_upto(x, m):
    """
    Evaluates Hermite polynomials 0 through M{m-1} at M{x}.

    @type    x:    number
    @param   x:    the point to evaluate the polynomials,
    @type    m:    integer
    @param   m:    the number of polynomials to evaluate.

    @return:    an N-array of the evaluated polynomials.
    """
    N        = x.shape[0]
    hermites = np.c_[np.ones((N, 1)), x, np.empty((N, m-2))]
    if m > 2:
        for i in range(2, m):
            hermites[:, i] = x * hermites[:, i-1] - (i-1) * hermites[:, i-2]
    return hermites


def lse(S_t, Y_tau, m, poly_type):
    """
    Calculate LSE M{a} in M{R^m} for problem M{Y_tau = S_t*a + err},
    where M{Y_tau} is the stopped payoff at stopping time M{tau^{bar}_{t+1}}
    for all paths M{omega_n}, M{n=1, ..., N} and M{S_t} is the
    stock price for all paths.

    @type    S_t:          N-array
    @param   S_t:          the stock price at time C{t} for all paths,
    @type    Y_tau:        N-array
    @param   Y_tau:        the stopped payoff at stopping time M{tau},
    @type    m:            integer
    @param   m:            the number of polynomials to evaluate,
    @type    poly_type:    string
    @param   poly_type:    the type of functions in the projection subspace, as recognised
                           by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.

    @return:    an array where the first element is the N-array LSE M{a}
                and the second element is the N-array of the projection
                M{Y_fit = S_t*a}.
    """
    poly_func = get_eval_func(poly_type)
    N         = S_t.shape[0]
    L         = poly_func(S_t, m)
    lse       = np.linalg.lstsq(L, Y_tau)
    proj      = np.mat(L)*np.mat(lse[0]).T
    return [lse[0], proj]
