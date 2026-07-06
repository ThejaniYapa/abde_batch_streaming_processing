"""Spout: emits a random sentence roughly once per second.

A spout is the *source* of a Storm stream. Storm calls `next_tuple` repeatedly;
each `emit` pushes one tuple downstream to the connected bolts.
"""
import random
import time

from streamparse import Spout


class RandomSentenceSpout(Spout):
    # Names of the fields in each tuple this spout emits.
    outputs = ["sentence"]

    def initialize(self, stormconf, context):
        self.sentences = [
            "apache storm stream processing",
            "real time word count demo",
            "event driven architecture",
            "python storm topology",
            "distributed stream processing",
        ]

    def next_tuple(self):
        sentence = random.choice(self.sentences)
        self.emit([sentence])
        time.sleep(1)  # throttle so the demo streams at a readable pace
