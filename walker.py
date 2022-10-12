import random

import pandas as pd
import networkx as nx
from itertools import product
from collections import defaultdict


class HIN:
    """
    Class to generate vertex sequences.
    """

    def __init__(self, window=None):
        self.graph = nx.DiGraph()
        self.node_size = 0
        self._path_size = 0

        def new_id():
            i = self.node_size
            self.node_size += 1
            return i

        self._node2id = defaultdict(new_id)
        self._id2type = {}
        self._window = window
        self._node_types = set()
        self._path2id = None
        self._id2path = None
        self._id2node = None

    @property
    def id2node(self):
        return self._id2node

    @property
    def id2path(self):
        return self._id2path

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, val):
        if not self._window:
            self._window = val
        else:
            raise ValueError("Error")

    @property
    def path_size(self):
        if not self._path_size:
            raise ValueError("run sample() first to count path size")
        return self._path_size

    def add_edge(self, source_node, source_class, dest_node, dest_class, edge_class, weight):
        i = self._node2id[source_node]
        j = self._node2id[dest_node]
        self._id2type[i] = source_class
        self._id2type[j] = dest_class
        self._node_types.add(source_class)
        self._node_types.add(dest_class)
        self.graph.add_edge(i, j, weight=weight)

    def small_walk(self, start_node, length):
        walk = [start_node]
        for i in range(1, length):
            if next(nx.neighbors(self.graph, walk[-1]), None) is None:
                break
            cur_node = walk[-1]
            nodes = list(nx.neighbors(self.graph, cur_node))
            weights = [self.graph[cur_node][i]['weight']
                       for i in nodes]
            s = sum(weights)
            weights = [i/s for i in weights]
            walk += random.choices(nodes, weights, k=1)
        return walk

    def do_walks(self, length):
        for start_node in range(self.node_size):
            yield self.small_walk(start_node, length)

    def sample(self, length, n_repeat):
        if not self.window:
            raise ValueError("window not set")

        if not self._path2id:
            self._path2id = {}
            path_id = 0
            for w in range(1, self._window + 1):
                for i in product(self._node_types, repeat=w + 1):
                    self._path2id[i] = path_id
                    path_id += 1

            self._path_size = len(self._path2id)
            self._id2node = {v: k for k, v in self._node2id.items()}
            self._id2path = {v: k for k, v in self._path2id.items()}

        samples = []

        for repeat in range(n_repeat):
            for walk in self.do_walks(length):
                cur_len = 0
                for i, node_id in enumerate(walk):
                    cur_len = min(cur_len + 1, self._window + 1)
                    if cur_len >= 2:
                        for path_length in range(1, cur_len):
                            sample = (walk[i - path_length], walk[i],
                                      self._path2id[tuple([self._id2type[t] for t in walk[i - path_length:i + 1]])])
                            samples.append(sample)

        return samples

    def print_statistics(self):
        print(f'size = {self.node_size}')


def load_a_HIN_from_pandas(edges, print_graph=False):
    def reverse(df):
        """
        reverse source & dest
        """
        df = df.rename({'source_node': 'dest_node', 'dest_node': 'source_node',
                        'source_class': 'dest_class', 'dest_class': 'source_class'},
                       axis=1)
        # reverse edge_class
        df.edge_class = df.edge_class.map(
            lambda x: '-'.join(reversed(x.split('-'))))
        return df

    print('load graph from edges...')
    g = HIN()
    if isinstance(edges, list):
        edges = pd.concat(edges, sort=False)
    edges = edges.append(reverse(edges), sort=False, ignore_index=True)

    for index, row in edges.iterrows():
        g.add_edge(row['source_node'], row['source_class'],
                   row['dest_node'], row['dest_class'], row['edge_class'],
                   row['weight'])
    if print_graph:
        g.print_statistics()
    print('finish loading graph!')
    return g
