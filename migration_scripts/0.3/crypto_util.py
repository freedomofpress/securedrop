# -*- coding: utf-8 -*-
# Minimal set of functions and variables from 0.2.1's crypto_util.py needed to
# regenerate journalist designations from soure's filesystem id's.
import random as badrandom

nouns = file("nouns.txt").read().split('\n')
adjectives = file("adjectives.txt").read().split('\n')

def displayid(n):
    badrandom_value = badrandom.WichmannHill()
    badrandom_value.seed(n)
    return badrandom_value.choice(adjectives) + " " + badrandom_value.choice(nouns)

