import networkx as nx


class GraphReader:
    def read(self, path):
        with open(path, 'r') as f:
            # next(f)
            persistence = 0.99
            graph = nx.Graph()
            for line in f:
                line = self.formatline(line)
                if line:  # The line that marks the switch is a blank line
                    if line[0] == 'N':
                        number_vertices = int(line[1])
                    elif line[0][0] == 'V':
                        vertexid = int(line[0][1:])
                        prob = float(line[2])
                        graph.add_node(vertexid, prob=prob)
                    elif line[0][0] == 'E':
                        edgeid = int(line[0][1:])
                        u = int(line[1])
                        v = int(line[2])
                        w = int(line[3][1:])
                        graph.add_edge(u, v, eid=edgeid, weight=w)
                    elif line[0] == 'Ppersistence':
                        persistence = float(line[1])
        return graph, persistence

    def formatline(self, line: str):
        if line.startswith('#'):
            return line[1:].split(';')[0].strip().split()  # Remove the comment if there is one and split into the parts
        else:  # The empty line that marks the switch from vertices to edges
            return ''
