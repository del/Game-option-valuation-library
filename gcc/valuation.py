#!/usr/bin/env python
# encoding: utf-8
"""
valuation.py

Created by Daniel Eliasson on 2009-06-02.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import numpy as np
from datetime import datetime
import polynomials as poly
from multiprocessing import Pool


def value_gcc(S, X, Y, r, T, **params):
    """
    Values a GCC. This function will delegate to C{value_single_threaded} unless
    C{params} has a key C{parallel} with value C{True}, and C{n_workers} with an
    integer value. Please note that the parallel processing always uses the no-lse
    method.
    """
    if "parallel" in params and params["parallel"] is True:
        return value_parallel(S, X, Y, r, T, **params)
    else:
        return value_single_threaded(S, X, Y, r, T, **params)


def value_single_threaded(S, X, Y, r, T, **params):
    """
    Values a GCC.

    @type        S:            (L+1) x N-array
    @param       S:            the simulated underlying paths. L is the number of time steps - 1
                               (timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
    @type        X:            (L+1) x N-array
    @param       X:            the payoffs to the option holder when the writer terminates,
    @type        Y:            (L+1) x N-array
    @param       Y:            the payoffs to the option holder when he exercises,
    @type        r:            number
    @param       r:            the risk-free interest rate,
    @type        T:            number
    @param       T:            the maturity time, measured in years,
    @param       params:       optional parameters,
    @type        m:            integer
    @keyword     m:            the number of dimensions in the projection subspace when using
                               the LSE method of valuation,
    @type        proj_type:    string
    @keyword     proj_type:    the type of functions in the projection subspace, as recognised
                               by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.

    @note:    When C{m} is set, the LSE method will be employed, otherwise not.
    @note:    Any further parameters will be ignored, but emitted into the output,
              so they can be used to annotate the output.
    @note:    The parameters C{S}, C{X}, and C{Y} must all be NumPy arrays with their shapes properly set.
              C{r} and C{T} will be cast to C{float64}.

    @return:  a C{dict} object containing all the input parameters, as well as:
                  - C{V}, the option price,
                  - C{var}, the Monte-Carlo variance
                  - C{dev}, the square root of var,
                  - C{L}, the number of time steps - 1,
                  - C{dt}, the size of a timestep, equal to T/L
                  - C{time}, the running time of the option pricing.
    """
    t0 = datetime.now()
    L  = S.shape[0] - 1
    r  = np.float64(r)
    T  = np.float64(T)
    dt = T/L

    # Use LSE method?
    lse_opts = {}
    if "m" in params:
        lse_opts["m"] = params["m"]
        if "proj_type" in params:
            lse_opts["proj_type"] = params["proj_type"]

    # Discount the payoff processes
    for j in range(1, L):
        X[j, :] = np.exp(-r*j*dt)*X[j, :]
        Y[j, :] = np.exp(-r*j*dt)*Y[j, :]

    sigma, tau = calculate_optimal_stopping_times(S, X, Y, lse_opts)
    V, var     = average_gcc_prices_over_paths(X, Y, sigma, tau)
    dev        = np.sqrt(var)
    t1         = datetime.now()

    params.update({
        "S":    S,
        "X":    X,
        "Y":    Y,
        "r":    r,
        "T":    T,
        "V":    V,
        "var":  var,
        "dev":  dev,
        "dt":   dt,
        "L":    L,
        "time": str(t1 - t0),
    })
    return params


def R(X, Y, sigma, tau, j):
    """
    Calculates the payoff M{R(sigma_j,tau_j)} from the GCC at time M{j}
    using the stopping strategies in C{sigma} and C{tau}.

    @type        X:          (L+1) x N-array
    @param       X:          the payoffs to the option holder when the writer terminates,
    @type        Y:          (L+1) x N-array
    @param       Y:          the payoffs to the option holder when he exercises,
    @type        sigma:      (L+1) x N-array
    @param       sigma:      the optimal stopping strategy for the writer of the option,
    @type        tau:        (L+1) x N-array
    @param       tau:        the optimal stopping strategy for the holder of the option,
    @type        j:          integer
    @param       j:          the time step to evaluate the payoff at.

    @return:    an N-array containing the payoffs.
    """
    N               = X.shape[1]
    I_sigma_lt_tau  = np.where(np.less(sigma[j, :], tau[j, :]), 1, 0)
    I_tau_lte_sigma = 1 - I_sigma_lt_tau
    R_sigma_tau_j   = X[sigma[j, :], range(N)]*I_sigma_lt_tau + Y[tau[j, :], range(N)]*I_tau_lte_sigma
    return R_sigma_tau_j


def exp_holding_value_lse(S, X, Y, sigma, tau, j, lse_opts):
    """
    Calculate the expected holding value M{E[R(sigma_{j+1}, tau_{j+1})|j]}
    by projecting M{R(sigma_{j+1}, tau_{j+1})} onto an M{m}-dimensional subspace
    of M{F_j}-measurable polynomial functions.

    @param       S:           the simulated underlying paths. L is the number of time steps - 1
                              (timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
    @type        X:           (L+1) x N-array
    @param       X:           the payoffs to the option holder when the writer terminates,
    @type        Y:           (L+1) x N-array
    @param       Y:           the payoffs to the option holder when he exercises,
    @type        sigma:       (L+1) x N-array
    @param       sigma:       the optimal stopping strategy for the writer of the option,
    @type        tau:         (L+1) x N-array
    @param       tau:         the optimal stopping strategy for the holder of the option,
    @type        j:           integer
    @param       j:           the time step to evaluate the payoff at,
    @type        lse_opts:    C{dict},
    @param       lse_opts:    a dictionary of options for the LSE,
    @type        m:           integer
    @keyword     m:           the number of dimensions in the projection subspace when using
                              the LSE method of valuation,
    @type        type:        string
    @keyword     type:        the type of functions in the projection subspace, as recognised
                              by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.

    @return:    an N-array containing the expected holding values.
    """
    N           = S.shape[1]
    R_sigma_tau = R(X, Y, sigma, tau, j+1)

    # Don't consider out-of-the-money paths
    S_j = S[j, :]
    for n in range(N):
        if Y[j, n] == 0:
            S_j[n]         = 0
            R_sigma_tau[n] = 0

    # Calculate expected holding value of option using LSE
    if "type" in lse_opts:
        lse = poly.lse(S_j, R_sigma_tau, lse_opts["m"], lse_opts["type"])
    else:
        lse = poly.lse(S_j, R_sigma_tau, lse_opts["m"], "laguerre")
    return lse[1]


def exp_holding_value_no_lse(S, X, Y, sigma, tau, j, lse_opts):
    """
    Let the expected holding value E[R(sigma_{j+1}, tau_{j+1})|j]
    simply be the exact R(sigma_{j+1}, tau_{j+1}).

    @param       S:           the simulated underlying paths. L is the number of time steps - 1
                              (timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
    @type        X:           (L+1) x N-array
    @param       X:           the payoffs to the option holder when the writer terminates,
    @type        Y:           (L+1) x N-array
    @param       Y:           the payoffs to the option holder when he exercises,
    @type        sigma:       (L+1) x N-array
    @param       sigma:       the optimal stopping strategy for the writer of the option,
    @type        tau:         (L+1) x N-array
    @param       tau:         the optimal stopping strategy for the holder of the option,
    @type        j:           integer
    @param       j:           the time step to evaluate the payoff at,
    @type        lse_opts:    C{dict},
    @param       lse_opts:    a dictionary that will be ignored, since LSE is not used here.

    @return:    an N-array containing the expected holding values.
    """
    R_sigma_tau = R(X, Y, sigma, tau, j+1)
    return R_sigma_tau


def calculate_optimal_stopping_times(S, X, Y, lse_opts={}):
    """
    Calculates optimal stopping strategies for the payoff
    M{R(sigma, tau) = X_sigma*I(sigma < tau) + Y_tau*I(tau <= sigma)}.

    @param       S:           the simulated underlying paths. L is the number of time steps - 1
                              (timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
    @type        X:           (L+1) x N-array
    @param       X:           the payoffs to the option holder when the writer terminates,
    @type        Y:           (L+1) x N-array
    @param       Y:           the payoffs to the option holder when he exercises,
    @type        lse_opts:    C{dict},
    @param       lse_opts:    a dictionary of options for the LSE, if it is to be used,
    @type        m:           integer
    @keyword     m:           the number of dimensions in the projection subspace when
                              using the LSE method of valuation,
    @type        type:        string
    @keyword     type:        the type of functions in the projection subspace, as recognised
                              by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.
    @note:    When C{m} is set, the LSE method will be employed, otherwise not.

    @return:    L x N-arrays C{sigma} and C{tau}, containing the optimal stopping strategies
                from each time point. E.g., C{sigma[j, :]} is the optimal stopping
                time restricted to M{{j+1, j+2, ..., L}} for the writer of the option.
    """
    L     = S.shape[0] - 1
    N     = S.shape[1]
    tau   = np.empty((L, N), dtype=np.int32)
    sigma = np.empty((L, N), dtype=np.int32)

    if "m" in lse_opts:
        exp_holding_value_func = exp_holding_value_lse
    else:
        exp_holding_value_func = exp_holding_value_no_lse

    """
    Beware below that while sigma and tau are indexed 0,...,L-1,
    they represent stopping times in 1,...,L. So if sigma_j = j,
    with the indexing scheme below, we get sigma[j] = j+1,
    since we're running j=L-1,...,0.
    """
    tau[L-1, :]   = L # tau_L = L for all paths
    sigma[L-1, :] = L
    for j in range(L-2,-1,-1): # j = L-1, ..., 1
        # Payoff if neither buyer nor seller exercises at j,
        # i.e. if exercise is at sigma_{j+1} or tau_{j+1}
        exp_holding_value = exp_holding_value_func(S, X, Y, sigma, tau, j, lse_opts)

        for n in range(N):
            # Out-of-the-money path
            if Y[j, n] == 0:
                tau[j, n]   = tau[j+1, n]
                sigma[j, n] = sigma[j+1, n]
                continue

            # Exercise value less than expected holding value
            if Y[j, n] < exp_holding_value[n]:
                tau[j, n] = tau[j+1, n]
            # Exercise value greater or equal to exp. holding value
            else:
                tau[j, n] = j+1

            # Termination value less than expected holding value
            if X[j, n] < exp_holding_value[n]:
                sigma[j, n] = j+1
            # Termination value greater or equal to exp. holding value
            else:
                sigma[j, n] = sigma[j+1, n]

    return sigma, tau


def average_gcc_prices_over_paths(X, Y, sigma, tau):
    """
    Calculates the option price at time 0 as the minimum of M{X_0}
    and the maximum of M{Y_0} and the average of M{R(sigma_1, tau_1)} over all paths.

    @type        X:          (L+1) x N-array
    @param       X:          the payoffs to the option holder when the writer terminates,
    @type        Y:          (L+1) x N-array
    @param       Y:          the payoffs to the option holder when he exercises,
    @type        sigma:      (L+1) x N-array
    @param       sigma:      the optimal stopping strategy for the writer of the option,
    @type        tau:        (L+1) x N-array
    @param       tau:        the optimal stopping strategy for the holder of the option,

    @return:    a tuple containing the option price and the sample variance.
    """
    N           = Y.shape[1]
    R_sigma_tau = R(X, Y, sigma, tau, 0) # R at optimal stops for all paths
    V_paths     = np.minimum(X[0, 0], np.maximum(Y[0, 0], R_sigma_tau))
    V           = np.min(np.array([X[0, 0], np.max(np.array([Y[0, 0], np.sum(R_sigma_tau)/N]))]))
    var         = np.sum(np.power(V_paths - V, 2))/(N-1)
    return V, var


def value_parallel(S, X, Y, r, T, **params):
    """
    Values a GCC.

    @type        S:            (L+1) x N-array
    @param       S:            the simulated underlying paths. L is the number of time steps - 1
                               (timesteps are numbered 0, 1, ..., L), and N is the number of simulated paths,
    @type        X:            (L+1) x N-array
    @param       X:            the payoffs to the option holder when the writer terminates,
    @type        Y:            (L+1) x N-array
    @param       Y:            the payoffs to the option holder when he exercises,
    @type        r:            number
    @param       r:            the risk-free interest rate,
    @type        T:            number
    @param       T:            the maturity time, measured in years,
    @param       params:       optional parameters,
    @type        m:            integer
    @keyword     m:            the number of dimensions in the projection subspace when using
                               the LSE method of valuation,
    @type        proj_type:    string
    @keyword     proj_type:    the type of functions in the projection subspace, as recognised
                               by L{gcc.polynomials}; e.g. C{"hermite"} or C{"laguerre"}.

    @note:    When C{m} is set, the LSE method will be employed, otherwise not.
    @note:    Any further parameters will be ignored, but emitted into the output,
              so they can be used to annotate the output.
    @note:    The parameters C{S}, C{X}, and C{Y} must all be NumPy arrays with their shapes properly set.
              C{r} and C{T} will be cast to C{float64}.

    @return:  a C{dict} object containing all the input parameters, as well as:
                  - C{V}, the option price,
                  - C{var}, the Monte-Carlo variance
                  - C{dev}, the square root of var,
                  - C{L}, the number of time steps - 1,
                  - C{dt}, the size of a timestep, equal to T/L
                  - C{time}, the running time of the option pricing.
    """
    t0 = datetime.now()
    L  = S.shape[0] - 1
    N  = S.shape[1]
    r  = np.float64(r)
    T  = np.float64(T)
    dt = T/L

    # Create list of parameter dictionaries to parallelise computation
    parameters = [(X[:, n], Y[:, n], L, n) for n in range(0, N-1)]

    # Create a pool of processes
    pool = Pool(params["n_workers"])

    # Calculate valuations from each path
    valuations = pool.map(value_no_lse, parameters)

    # Calculate average valuation and the variance
    V   = np.mean(valuations)
    var = np.var(valuations)
    dev = np.sqrt(var)

    t1  = datetime.now()

    params.update({
        "S":    S,
        "X":    X,
        "Y":    Y,
        "r":    r,
        "T":    T,
        "V":    V,
        "var":  var,
        "dev":  dev,
        "dt":   dt,
        "L":    L,
        "time": str(t1 - t0),
    })
    return params


def value_no_lse(params):
    X_n               = params[0]
    Y_n               = params[1]
    L                 = params[2]
    n                 = params[3]
    exp_holding_value = Y_n[L]
    for j_p in range(L-1, -1, -1): # j = L-1, ..., 1
        if Y_n[j_p] == 0:
            continue

        if Y_n[j_p] > exp_holding_value:
            exp_holding_value = Y_n[j_p]
            continue

        if X_n[j_p] < exp_holding_value:
            exp_holding_value = X_n[j_p]

    return exp_holding_value
