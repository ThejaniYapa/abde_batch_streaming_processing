from streamparse import Topology
from spouts.random_sentence_spout import RandomSentenceSpout
from bolts.split_sentence_bolt import SplitSentenceBolt
from bolts.word_count_bolt import WordCountBolt

class WordCountTopology(Topology):

    random_sentence_spout = RandomSentenceSpout.spec(
        parallelism=1
    )

    split_sentence_bolt = SplitSentenceBolt.spec(
        inputs=[random_sentence_spout],
        parallelism=2
    )

    word_count_bolt = WordCountBolt.spec(
        inputs=[split_sentence_bolt],
        parallelism=2
    )
