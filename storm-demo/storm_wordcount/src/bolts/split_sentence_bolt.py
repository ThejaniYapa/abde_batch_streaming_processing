from streamparse import Bolt

class SplitSentenceBolt(Bolt):
    outputs = ["word"]

    def process(self, tup):
        sentence = tup.values[0]
        for word in sentence.split():
            self.emit([word])
