"""Bolt: keeps a running count of every word it sees.

State (`self.counts`) lives for the lifetime of the bolt instance, so counts
accumulate across tuples. Each update is emitted downstream and logged so you
can watch the counts climb in the worker logs.
"""
from collections import defaultdict

from streamparse import Bolt


class WordCountBolt(Bolt):
    outputs = ["word", "count"]

    def initialize(self, conf, ctx):
        self.counts = defaultdict(int)

    def process(self, tup):
        word = tup.values[0]
        self.counts[word] += 1
        self.emit([word, self.counts[word]])
        self.log(f"{word} -> {self.counts[word]}")
