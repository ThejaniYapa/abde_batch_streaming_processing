"""Word-count topology.

Wires the spout and bolts into a streaming DAG:

    RandomSentenceSpout ──▶ SplitSentenceBolt ──▶ WordCountBolt

Notes for streamparse:
  * `.spec()` takes parallelism as `par=` (NOT `parallelism=`).
  * `inputs=[...]` connects a bolt to its upstream component.
"""
from streamparse import Topology

from spouts.random_sentence_spout import RandomSentenceSpout
from bolts.split_sentence_bolt import SplitSentenceBolt
from bolts.word_count_bolt import WordCountBolt


class WordCountTopology(Topology):

    random_sentence_spout = RandomSentenceSpout.spec(
        par=1,
    )

    split_sentence_bolt = SplitSentenceBolt.spec(
        inputs=[random_sentence_spout],
        par=2,
    )

    word_count_bolt = WordCountBolt.spec(
        inputs=[split_sentence_bolt],
        par=2,
    )
