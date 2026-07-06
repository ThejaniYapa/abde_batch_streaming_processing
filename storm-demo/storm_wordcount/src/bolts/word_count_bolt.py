from streamparse import Bolt
from collections import defaultdict

class WordCountBolt(Bolt):
    outputs = ["word", "count"]

    def initialize(self, conf, ctx):
        self.counts = defaultdict(int)

    def process(self, tup):
        word = tup.values[0]
        self.counts[word] += 1
        self.emit([word, self.counts[word]])
        self.log(f"{word} -> {self.counts[word]}")
