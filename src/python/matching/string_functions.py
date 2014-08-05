import os, sys, inspect
sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],".."))))
import argparse
from pprint import pprint
import logging
from nltk import metrics, stem, tokenize
from nltk.tokenize import WhitespaceTokenizer
import string
import re


def normalize(s):
    s = s.replace("|", "")
    for p in string.punctuation:
        s = s.replace(p, ' ')
    s = re.sub(r'[ ]{2,}', " ", s)
    return s.lower().strip()

    

def tokenize(s):
    return WhitespaceTokenizer().tokenize(s)

def shinglize(s, n = 2, tokenizer=tokenize):
    """
    return size n shingles for the string s
    """
    shingles = set()
    tokens = tokenizer(s)
    for i in range(len(tokens) - n + 1):
        shingles.add('_'.join(tokens[i:i+n]))
    return shingles
    
def jaccard_distance(s1, s2):
    return (len(s1.intersection(s2)) * 1.0) / max(1,len(s1.union(s2)) )
    
def is_prefix(pattern, text, normalizer=normalize):
    """
    checks if pattern is a prefix of text
    """
    if normalizer:
        pattern = normalize(pattern)
        text = normalize(text)
    return text.startswith(pattern)
    
def is_postfix(pattern, text, normalizer=normalize):
    """
    checks if pattern is a prefix of text
    """
    if normalizer:
        pattern = normalize(pattern)
        text = normalize(text)
    return text.endswith(pattern)
    