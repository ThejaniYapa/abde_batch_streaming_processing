"""Bolt: splits each incoming sentence into individual words.

A bolt consumes tuples and (optionally) emits new ones. Storm calls `process`
once per incoming tuple. Here one sentence fans out into many word tuples.
"""
from streamparse import Bolt


class SplitSentenceBolt(Bolt):
    outputs = ["word"]

    def process(self, tup):
        sentence = tup.values[0]
        for word in sentence.split():
            self.emit([word])
