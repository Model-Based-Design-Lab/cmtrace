"""A library for maxplus algebra and signals."""

from functools import reduce


# quick and dirty implementation of MPMINUSINFINITY
MPMINUSINF = -1000
MPMINUSTHRESHOLD = MPMINUSINF >> 1

# special value to denote the infinitely long sequence of MINUSINF values
# the neutral element of max over sequences.
ZEROSEQ = -1

def delay(events, number_of_tokens, initial_time=MPMINUSINF):
    """Delay an event sequence by n tokens. n may be negative, in which case tokens will be removed."""
    if number_of_tokens >= 0:
        return initialtokens(number_of_tokens, initial_time) + events
    else:
        return events[-number_of_tokens:]


def initialtokens(number_of_tokens, initial_time=MPMINUSINF):
    """
    Return an event sequence of the given length with -infty values, or a specific value
    passed as the second argument
    """
    return [initial_time] * number_of_tokens

def mpmax2(seq1, seq2):
    """Compute the max operation on two event sequences."""
    return list(map(lambda l: max(l), zip(seq1, seq2)))


def mpmax(*args):
    """Compute the max operation on an arbitrary number of sequences"""
    if len(args) == 0:
        return ZEROSEQ
    return reduce(lambda s1, s2: mpmax2(s1, s2), args)

def mpplus(seq, timedelay):
    """Add a time delay to a sequence"""
    return [x+timedelay for x in seq]

def output_sequence(input_sequence, initial_tokens, arcdelay, initial_time=MPMINUSINF):
    """Apply a token delay and a time delay to a sequence"""
    return mpplus(delay(input_sequence, initial_tokens, initial_time), arcdelay)

def trace(seq, duration, tracelen):
    """Create a string representation of an execution trace of the
    given length with starting times in seq, with firings of the given duration. """
    tracestr = ''
    newseq = list(seq) + [1000]
    for k in range(tracelen):
        if len(newseq) == 0:
            return tracestr
        while newseq[0]+duration <= k:
            newseq = newseq[1:]
        if k < newseq[0]:
            tracestr += '-'
        else:
            tracestr += '*'
    return tracestr

