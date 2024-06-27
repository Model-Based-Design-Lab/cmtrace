"""A library for maxplus algebra and signals."""

from functools import reduce


# quick and dirty implementation of MP_MINUS_INFINITY
MP_MINUS_INF = -1000
MP_MINUS_THRESHOLD = MP_MINUS_INF >> 1

# special value to denote the infinitely long sequence of MINUS_INF values
# the neutral element of max over sequences.
ZERO_SEQ = -1

def delay(events, number_of_tokens, initial_time=MP_MINUS_INF):
    """Delay an event sequence by n tokens. n may be negative, in which case tokens
    will be removed."""
    if number_of_tokens >= 0:
        return get_initial_tokens(number_of_tokens, initial_time) + events
    return events[-number_of_tokens:]


def get_initial_tokens(number_of_tokens, initial_time=MP_MINUS_INF):
    """
    Return an event sequence of the given length with -infty values, or a specific value
    passed as the second argument
    """
    return [initial_time] * number_of_tokens

def mp_max2(seq1, seq2):
    """Compute the max operation on two event sequences."""
    return list(map(max, zip(seq1, seq2)))


def mp_max(*args):
    """Compute the max operation on an arbitrary number of sequences"""
    if len(args) == 0:
        return ZERO_SEQ
    return reduce(mp_max2, args)

def mp_plus(seq, time_delay):
    """Add a time delay to a sequence"""
    return [x+time_delay for x in seq]

def output_sequence(input_sequence, initial_tokens, arc_delay, initial_time=MP_MINUS_INF):
    """Apply a token delay and a time delay to a sequence"""
    return mp_plus(delay(input_sequence, initial_tokens, initial_time), arc_delay)

def trace(seq, duration, trace_len):
    """Create a string representation of an execution trace of the
    given length with starting times in seq, with firings of the given duration. """
    trace_str = ''
    newseq = list(seq) + [1000]
    for k in range(trace_len):
        if len(newseq) == 0:
            return trace_str
        while newseq[0]+duration <= k:
            newseq = newseq[1:]
        if k < newseq[0]:
            trace_str += '-'
        else:
            trace_str += '*'
    return trace_str
