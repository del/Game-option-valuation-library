#!/usr/bin/env python
# encoding: utf-8
"""
security_simulation.py

Created by Daniel Eliasson on 2009-04-30.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import numpy as np
import numpy.random
import storage


def black_scholes(S0, r, volatility, T, N, L, rand_gen_state=None):
    """
    Generates paths for M{S} in risk-neutral Black-Scholes formulation:
    M{dS = r(t)*S(t)*dt + volatility*S(t)*dW_t}

    Generates M{N/2} paths plus their antithetic paths, so a total
    of M{N} paths are returned. If M{N} is odd, an error is raised.
    Note that the time steps are numbered M{j=0,...,L}, giving M{L+1}
    time steps in total.

    @type    S0:               number
    @param   S0:               the starting value of the generated paths,
    @type    r:                number
    @param   r:                the risk-free interest rate,
    @type    volatility:       number
    @param   volatility:       the volatility of the underlying,
    @type    T:                number
    @param   T:                the maturity time, measured in years,
    @type    N:                integer
    @param   N:                the number of paths to generate,
    @type    L:                integer
    @param   L:                the number of time steps,
    @param   rand_gen_state:   NumPy random number generator state object.

    @return:    a tuple containing a (L+1) x N-array of paths, and the
                random number generator state used to generate the paths.
    """
    if rand_gen_state is not None:
        np.random.set_state(rand_gen_state)
    rand_gen_state = np.random.get_state()
    dt = np.float64(T)/L
    if N % 2 != 0:
        raise "N must be divisible by 2"

    eps = np.random.normal(size=(L, N/2))
    eps = np.hstack((eps, -eps)) # Add antithetic paths

    S = np.vstack((S0*np.ones((1, N)), S0*np.exp(np.cumsum((r - np.power(volatility, 2)/2)*dt + volatility*np.sqrt(dt)*eps, 0))))
    return S, rand_gen_state


def jump_diffusion(S0, r, volatility, d, eta, theta, T, N, L, rand_gen_state=None):
    """
    Generates paths for M{S} in a risk-neutral jump-diffusion with
    non-negative, exponentially distributed jumps, and continuous
    dividend payment.

    M{S_t = exp(volatility*W_t + mu*t + J_t)}
    where M{W} is a Wiener process, M{J} a compound Poisson process with
    jump intensity M{eta > 0} and increments following exponential distribution
    with parameter M{theta > 1}, and M{mu = r - d - volatility^2/2 + eta/(1-theta)}.

    @type    S0:               number
    @param   S0:               the starting value of the generated paths,
    @type    r:                number
    @param   r:                the risk-free interest rate,
    @type    volatility:       number
    @param   volatility:       the volatility of the underlying,
    @type    d:                number
    @param   d:                the continuous dividend payment rate of the underlying,
    @type    eta:              number
    @param   eta:              jump intensity of the underlying,
    @type    theta:            number
    @param   theta:            exponential distribution parameter of the jump sizes,
    @type    T:                number
    @param   T:                the maturity time, measured in years,
    @type    N:                integer
    @param   N:                the number of paths to generate,
    @type    L:                integer
    @param   L:                the number of time steps,
    @param   rand_gen_state:   NumPy random number generator state object.

    @return:    a tuple containing a (L+1) x N-array of paths, and the
                random number generator state used to generate the paths.
    """
    if rand_gen_state is not None:
        np.random.set_state(rand_gen_state)
    rand_gen_state = np.random.get_state()
    dt = np.float64(T)/L
    if N % 2 != 0:
        raise "N must be divisible by 2"

    # Simulate Wiener process diffusion and drift
    eps = np.random.normal(size=(L, N/2))
    eps = np.hstack((eps, -eps)) # Add antithetic paths
    mu_and_W = np.cumsum((r - d - np.power(volatility, 2)/2 + eta/(1-theta))*dt + volatility*np.sqrt(dt)*eps, 0)

    # Simulate the jump process pathwise
    beta_times = 1.0/eta
    beta_jumps = 1.0/theta
    J = np.zeros((L, N))
    for n in range(N):
        cum_jumps = np.random.exponential(beta_times)
        for j in range(L):
            t = (j+1)*dt
            J[j, n] = np.copy(J[j-1, n])
            while t > cum_jumps:
                J[j, n] += np.random.exponential(beta_jumps)
                cum_jumps += np.random.exponential(beta_times)

    # Build the process S
    S = np.vstack((S0*np.ones((1, N)), S0*np.exp(mu_and_W + J)))
    return S, rand_gen_state
