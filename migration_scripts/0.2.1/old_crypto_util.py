# -*- coding: utf-8 -*-
# Minimal set of functions and variables from 0.2.1's crypto_util.py needed to
# regenerate journalist designations from soure's filesystem id's.
import os
import random as badrandom

# Find the absolute path relative to this file so this script can be run
# anywhere
SRC_DIR = os.path.dirname(os.path.realpath(__file__))

nouns = file(os.path.join(SRC_DIR, "nouns.txt")).read().split('\n')
adjectives = file(os.path.join(SRC_DIR, "adjectives.txt")).read().split('\n')


def displayid(n):
    badrandom_value = badrandom.WichmannHill()
    badrandom_value.seed(n)
    return badrandom_value.choice(
        adjectives) + " " + badrandom_value.choice(nouns)
