#!/usr/bin/env python
# encoding: utf-8
"""
example_parallel.py

Created by Daniel Eliasson on 2012-02-26.
Copyright (c) 2012 Daniel Eliasson. All rights reserved.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
import getopt
import gcc.storage
import gcc.security_simulation
from gcc.claims import *
from datetime import datetime
from multiprocessing import Pool


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


help_message = '''
Usage:
python example_parallel.py -b/--batch-dir batch_dir_name [-n/--no-lse] -t type [-w/--workers n]

-t/--type         one of game-call, game-put, callable-put or convertible-bond

-b/--batch-dir    the directory where the output will be saved

-n/--no-lse       use the LSE-free version of the algorithm

-w/--workers n    number of parallel processes (default 6)
'''


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "b:hnt:w:",
                ["batch-dir=", "help", "no-lse", "type=", "workers="])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        batch_dir   = None
        no_lse      = False
        option_type = None
        n_workers   = 6
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-b", "--batch-dir"):
                batch_dir = value.strip()
            if option in ("-n", "--no-lse"):
                no_lse = True
            if option in ("-t", "--type"):
                option_type = value.strip()
            if option in ("-w", "--workers"):
                n_workers = int(value.strip())
        if batch_dir is None or option_type is None:
            raise Usage(help_message)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

    if no_lse:
        m_tuple = (None,)
    else:
        m_tuple = (60,)#(8, 16)

    # Risk-free interest rate and volatility of the underlying
    r          = 0.06
    volatility = 0.4

    # Callable put parameters
    K     = 100
    delta = 5
    T     = 0.5

    t0           = datetime.now()
    run_specs    = []
    #for N in (1000, 2000, 4000, 8000):
    for N in (1000,):
        #for L in (101, 201, 401, 801, 1601, 3201):
        for L in (101,):
            for m in m_tuple:
                #for S0 in (80, 90, 100, 110, 120):
                for S0 in (80, 90, 110, 120):
                    for i in range(1, 14):
                        run_specs.append((N, L, m, S0, r, volatility, K, delta, T, option_type, batch_dir))

    pool = Pool(n_workers)
    pool.map(perform_valuation, run_specs)
    t1 = datetime.now()

    print "Performed", len(run_specs), " valuations in ", str(t1 - t0), " seconds."
    print "Valuations saved in ", batch_dir


def perform_valuation(run_spec):
    N           = run_spec[0]
    L           = run_spec[1]
    m           = run_spec[2]
    S0          = run_spec[3]
    r           = run_spec[4]
    volatility  = run_spec[5]
    K           = run_spec[6]
    delta       = run_spec[7]
    T           = run_spec[8]
    option_type = run_spec[9]
    batch_dir   = run_spec[10]

    print "N =", N, "  L =", L, "  m =", m
    print "K =", K, "  delta =", delta, "  T =", T, "  r = ", r, "  volatility = ", volatility

    # Generate the stock paths using Black-Scholes model
    S, rand_gen_state = gcc.security_simulation.black_scholes(S0=S0,
                                                              r=r,
                                                              volatility=volatility,
                                                              T=T,
                                                              N=N,
                                                              L=L)

    # Build parameter dictionary
    params = {
        "S0": S0, "S": S, "r": r, "volatility": volatility, "T": T,
        "N": N, "L": L, "K": K, "delta": delta
    }

    # Valuation
    if m is not None:
        params.update({"m": m})

    if option_type == "game-put":
        valuation = gcc.claims.game_put_option.value(**params)
    elif option_type == "game-call":
        valuation = gcc.claims.game_call_option.value(**params)
    elif option_type == "callable-put":
        valuation = gcc.claims.callable_put.value(**params)
    elif option_type == "convertible-bond":
        valuation = gcc.claims.convertible_bond.value(**params)

    print "Option price: V =", valuation["V"], "  Var =", valuation["var"], "  dev =", valuation["dev"], "calculated in", valuation["time"], "\n\n"
    batch_dir, filename = gcc.storage.save_valuation_json(valuation, batch_dir)


if __name__ == '__main__':
    main()
