#!/usr/bin/env python
# encoding: utf-8
"""
game_call_option_example.py

Created by Daniel Eliasson on 2009-09-10.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import sys
import getopt
sys.path.append('..')
import gcc.storage
import gcc.security_simulation
import gcc.claims.game_call_option


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


help_message = '''
Usage:
python game_call_option_example.py -b/--batch-dir batch_dir_name [-n/--no-lse]

-b/--batch-dir    the directory where the output will be saved

-n/--no-lse       use the LSE-free version of the algorithm
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
        m_tuple = (8, 16)

    # Risk-free interest rate and volatility of the underlying
    r          = 0.06
    volatility = 0.4

    # Callable put parameters
    K     = 100
    delta = 10
    T     = 0.5

    t0           = datetime.now()
    n_valuations = 0
    for N in (1000, 2000, 4000, 8000):
        for L in (101, 201):
            for m in m_tuple:
                for S0 in (80, 90, 100, 110, 120):
                    print "N =", N, "  L =", L, "  m =", m
                    print "K =", K, "  delta =", delta, "  T =", T, "  r = ", r, "  volatility = ", volatility

                    # Generate the stock paths using Black-Scholes model
                    S, rand_gen_state = gcc.security_simulation.black_scholes(S0=S0, r=r, volatility=volatility, T=T, N=N, L=L)

                    # Build parameter dictionary
                    params = {
                        "S0": S0, "S": S, "r": r, "volatility": volatility, "T": T,
                        "N": N, "L": L, "K": K, "delta": delta
                    }

                    # Value the callable put
                    if not no_lse:
                        params.update({"m": m})
                    valuation = gcc.claims.game_call_option.value(**params)

                    print "Option price: V =", valuation["V"], "  Var =", valuation["var"], "  dev =", valuation["dev"], "calculated in", valuation["time"], "\n\n"
                    batch_dir, filename = gcc.storage.save_valuation_json(valuation, batch_dir)
    print "Valuations saved in ", batch_dir


if __name__ == '__main__':
    main()

