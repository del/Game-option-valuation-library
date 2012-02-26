#!/usr/bin/env python
# encoding: utf-8
"""
create_example_graphs.py

Created by Daniel Eliasson on 2009-04-30.
Copyright (c) 2009 Daniel Eliasson. All rights reserved.
"""

import sys
import os
import getopt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
sys.path.append("..")
import gcc.security_simulation
import gcc.storage


def bs_path_graph(N, graph_dir):
    T     = 1.0
    L     = 365
    S0    = 100
    r     = 0.15
    sigma = 0.20

    S, gen_state = gcc.security_simulation.black_scholes(S0, r, sigma, T, N, L)

    fig = plt.figure()
    sp = fig.add_subplot(111)
    sp.plot(S)
    sp.plot(range(S.shape[0]), S0*np.ones_like(S[:, 1]), color="black", linestyle="dashed")
    sp.plot([0, L+1], [S0, S0*(1+r)], color="#777777", linestyle="dashed") # plot drift

    sp.set_title("%i simulated paths for stock"%N)

    # Format x axis
    sp.set_xlim([0, 365])
    sp.set_xticks(np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]))
    sp.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

    # Format y axis to have ticks to the right and in green
    # with the format Rxx.xx
    sp.set_ylabel("Stock price")
    sp.yaxis.set_major_formatter(ticker.FormatStrFormatter("R%1.2f"))
    for tick in sp.yaxis.get_major_ticks():
        tick.label1On = False
        tick.label2On = True
        tick.label2.set_color('green')

    # Save plots
    gcc.storage.ensure_dir_exists(graph_dir)
    fig.savefig(os.path.join(graph_dir, "bs_path_graph.png"))


def jump_diffusion_path_graph(N, graph_dir):
    T          = 1.0
    L          = 365
    S0         = 100
    r          = 0.06
    d          = 0.02
    eta        = 10
    theta      = 7
    volatility = 0.40

    S, gen_state = gcc.security_simulation.jump_diffusion(S0, r, volatility, d, eta, theta, T, N, L)

    fig = plt.figure()
    sp = fig.add_subplot(111)
    sp.plot(S)
    sp.plot(range(S.shape[0]), S0*np.ones_like(S[:, 1]), color="black", linestyle="dashed")

    sp.set_title("%i simulated paths for stock"%N)

    # Format x axis
    sp.set_xlim([0, L])
    sp.set_xticks(np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]))
    sp.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

    # Format y axis to have ticks to the right and in green
    # with the format Rxx.xx
    sp.set_ylabel("Stock price")
    sp.yaxis.set_major_formatter(ticker.FormatStrFormatter("R%1.2f"))
    for tick in sp.yaxis.get_major_ticks():
        tick.label1On = False
        tick.label2On = True
        tick.label2.set_color('green')

    # Save plots
    gcc.storage.ensure_dir_exists(graph_dir)
    fig.savefig(os.path.join(graph_dir, "jump_diffusion_path_graph.png"))


def gcc_graphs(graph_dir, N=1):
    N      = N*2
    T      = 1.0
    L      = 364
    strike = 102
    S0     = 100
    r      = 0.015
    sigma  = 0.20

    # Generate underlying path and calculate option payoffs
    S, gen_state = gcc.security_simulation.black_scholes(S0, r, sigma, T, N, L)
    Y            = np.maximum(S - strike, 0) # exercise
    Z            = Y + 10 # termination

    for n in range(N/2): # Don't plot antithetic paths
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4)

        # Plot stock price
        sp = fig.add_subplot(211)
        sp.plot(range(S.shape[0]), S[:, n], "m")
        sp.plot(range(S.shape[0]), strike*np.ones_like(S[:, n]), color="#cccccc", linestyle="dashed") # plot strike price

        # Format x axis
        sp.set_xlim([0, L+1])
        sp.set_xticks(np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]))
        sp.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

        # Format y axis to have ticks to the right and in green
        # with the format Rxx.xx
        sp.set_ylabel("Stock price")
        sp.yaxis.set_major_formatter(ticker.FormatStrFormatter("R%1.2f"))
        for tick in sp.yaxis.get_major_ticks():
            tick.label1On = False
            tick.label2On = True
            tick.label2.set_color('green')

        # Plot payoff
        sp = fig.add_subplot(212)
        sp.plot(range(S.shape[0]), Y[:, n], "g", range(L+1), Z[:, n], "r")
        sp.set_ylabel("Option payoff")

        # Format x axis
        sp.set_xlim([0, L])
        sp.set_xticks(np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]))
        sp.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

        # Format y axis to have ticks to the right and in green
        # with the format Rxx.xx
        sp.yaxis.set_major_formatter(ticker.FormatStrFormatter("R%1.2f"))
        for tick in sp.yaxis.get_major_ticks():
            tick.label1On = False
            tick.label2On = True
            tick.label2.set_color('green')
        sp.set_ylim([0, sp.get_ylim()[1] + 4]) # make room for legend

        # Legend
        legend = sp.legend(("Exercise", "Termination"), "upper left", shadow=True)
        for t in legend.get_texts():
            t.set_fontsize('small')
        for l in legend.get_lines():
            l.set_linewidth(1.5)

        # Annotate optimal exercise point
        max_exercise_payoff = np.max(Y[:, n])
        max_exercise_date = np.where(Y[:, n] == max_exercise_payoff)[0][0]
        if max_exercise_payoff > 0:
            if max_exercise_payoff > sp.get_ylim()[1]/2:
                xytext = (-30, -60)
            else:
                xytext = (-30, 60)
            sp.annotate("Optimal exercise time", xy=(max_exercise_date, max_exercise_payoff),
                        xytext=xytext, textcoords="offset points", arrowprops=dict(arrowstyle="->"), size=10)

        # Save plots
        gcc.storage.ensure_dir_exists(graph_dir)
        fig.savefig(os.path.join(graph_dir, "price_and_payoff_%i.png"%n))


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


help_message = '''
Usage:
python draw_some_example_graphs.py -g/--graph-dir graph_dir

-g/--graph-dir    the directory where the graphs will be saved
'''

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "g:h",
                ["graph-dir=", "help"])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        graph_dir = None
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-g", "--graph-dir"):
                graph_dir = value.strip()
        if graph_dir is None:
            raise Usage(help_message)

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

    bs_path_graph(20, graph_dir)
    jump_diffusion_path_graph(20, graph_dir)
    gcc_graphs(graph_dir, 4)


if __name__ == '__main__':
    main()

