import math


def get_pad(name):
    return (math.ceil((len(name) + 1) / 4) * 4) - (len(name) + 1)