from streamparse import Spout
import random
import time

class RandomSentenceSpout(Spout):
    outputs = ["sentence"]

    def initialize(self, stormconf, context):
        self.sentences = [
            "apache storm stream processing",
            "real time word count demo",
            "event driven architecture",
            "python storm topology",
            "distributed stream processing"
        ]

    def next_tuple(self):
        sentence = random.choice(self.sentences)
        self.emit([sentence])
        time.sleep(1)  # simulate live streaming
