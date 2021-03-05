import math

import networkx as nx


def normalize(odds):
    alpha = 1.0 / (sum(odds))
    normalized_odds = [x * alpha for x in odds]
    return normalized_odds


class DBNBuilder:
    def __init__(self, graph, p):
        self.graph = graph
        self.persistence = p
        self.dbn = None
        self.need_to_update = False
        self.curr_time = -1
        self.id = 0

    def create_dbn(self):
        dbn = nx.DiGraph()
        self.dbn = dbn
        for e in self.graph.edges(data=True):
            v_ids = []
            for i in range(2):
                vid = e[i]
                already_added = False
                for node in dbn.nodes(data=True):
                    if node[1]['type'] == 'people_in_node' and node[1]['vid'] == vid:
                        already_added = True
                        v_ids.append(node[0])
                        break
                if not already_added:
                    dbn.add_node(self.id, type='people_in_node', vid=vid,
                                 prob=self.graph.nodes(data=True)[e[i]]['prob'])
                    v_ids.append(self.id)
                    self.id += 1
            edge_id = self.id
            self.id += 1
            dbn.add_node(edge_id, type='is_edge_blocked', eid=e[2]['eid'], weight=e[2]['weight'], time=0)
            self.create_truth_table_for_initial_edge(edge_id)
            dbn.add_edge(v_ids[0], edge_id)
            dbn.add_edge(v_ids[1], edge_id)
        self.curr_time = 0

    def create_truth_table_for_initial_edge(self, node_id):
        d = {}
        # Both dont have people
        node_data = self.dbn.nodes(data=True)[node_id]
        d['prob_both_no_people'] = 0.001
        # Only u has people
        d['prob_only_u'] = (1 - (1 - 0.6 / node_data['weight']))
        # Only v has people
        d['prob_only_v'] = (1 - (1 - 0.6 / node_data['weight']))
        # Both have people
        d['prob_both_with_people'] = (1 - math.pow(1 - 0.6 / node_data['weight'], 2))
        node_data['truth_table'] = d

    def advance_time(self, time_slices=1):
        for _ in range(time_slices):
            to_add = []
            for node in self.dbn.nodes(data=True):
                if node[1]['type'] == 'is_edge_blocked' and node[1]['time'] == self.curr_time:
                    to_add.append({'eid': node[1]['eid'], 'weight': node[1]['weight'], 'node_id': node[0]})
            d = {'was_blocked': self.persistence, 'was_free': 0.001}
            for node in to_add:
                self.dbn.add_node(self.id, type='is_edge_blocked', eid=node['eid'], weight=node['weight'],
                                  time=self.curr_time + 1, truth_table=d)
                self.dbn.add_edge(node['node_id'], self.id)
                self.id += 1
            self.curr_time += 1

    def print_network_structure(self):
        if self.dbn is None:
            print("No DBN created, returning")
            return
        for node in self.dbn.nodes(data=True):
            if node[1]['type'] == 'people_in_node':
                print(f"VERTEX {node[1]['vid']}")
                print(f"\tP(Evacuees {node[1]['vid']}) = {node[1]['prob']}")
                print(f"\tP(not Evacuees {node[1]['vid']}) = {1 - node[1]['prob']}")
        for node in self.dbn.nodes(data=True):
            if node[1]['type'] == 'is_edge_blocked':
                if node[1]['time'] == 0:
                    print(f"Edge {node[1]['eid']}, time {node[1]['time']}:")
                    print(
                        f"\tP(Blockage | no people at 1, no people at 2) = {node[1]['truth_table']['prob_both_no_people']}")
                    print(f"\tP(Blockage | people at 1, no people at 2) = {node[1]['truth_table']['prob_only_u']}")
                    print(f"\tP(Blockage | no people at 1, people at 2) = {node[1]['truth_table']['prob_only_v']}")
                    print(
                        f"\tP(Blockage | people at 1, people at 2) = {node[1]['truth_table']['prob_both_with_people']}")
                else:
                    print(f"Edge {node[1]['eid']}, time {node[1]['time']}:")
                    print(
                        f"\tP(Blockage | was blocked at {node[1]['time'] - 1}) = {node[1]['truth_table']['was_blocked']}")
                    print(f"\tP(Blockage | was free at {node[1]['time'] - 1}) = {node[1]['truth_table']['was_free']}")

    def enumerate_ask(self, node, evidence):
        odds = []
        if node in evidence.keys():
            if evidence[node]:
                return [1, 0]
            else:
                return [0, 1]
        relevant_vars = self.get_relevant_vars(node, evidence)
        for val in [True, False]:
            evidence[node] = val
            odds.append(self.enumerate_all(relevant_vars, evidence))
        odds = normalize(odds)
        return odds

    def get_relevant_vars(self, q, e):
        current_network = nx.DiGraph(self.dbn)
        while True:
            # print(f"current relevant vars are {relevant_vars}")
            to_remove = []
            for node in current_network.nodes():
                if current_network.out_degree(node) == 0 and node not in e.keys() and node != q:
                    to_remove.append(node)
            if len(to_remove) == 0:
                break
            else:
                for n in to_remove:
                    current_network.remove_node(n)
        relevant_vars = [x[0] for x in current_network.nodes(data=True)]
        relevant_vars.sort()
        return relevant_vars

    def enumerate_all(self, relevant_vars, evidence):
        if not relevant_vars:
            return 1
        some_var = relevant_vars[0]
        # Check if we have any evidence about it
        if some_var in evidence.keys():
            # If it has some value than we need to give the probability it has that value given the variables
            return self.odds_given_value(some_var, evidence) * self.enumerate_all(relevant_vars[1:], dict(evidence))
        else:
            # Each variable has two possible values, check probabilities for both
            evidence[some_var] = True
            pos = self.odds_given_value(some_var, dict(evidence)) * self.enumerate_all(relevant_vars[1:],
                                                                                       dict(evidence))
            evidence[some_var] = False
            neg = self.odds_given_value(some_var, dict(evidence)) * self.enumerate_all(relevant_vars[1:],
                                                                                       dict(evidence))
            return pos + neg

    def odds_given_value(self, node_id, evidence):
        # Calculate the conditional probability of the queried variable being a certain value, given the evidence
        # Assumes that the quarried variable is already in evidence
        prob = -1
        node = self.dbn.nodes(data=True)[node_id]
        if node['type'] == 'people_in_node':
            # Vertices have no predecessors
            prob = node['prob']
        else:
            # This is an edge
            predecessors = self.dbn.predecessors(node_id)
            pred_trues = 0
            for p in predecessors:
                if evidence[p]:
                    pred_trues += 1
            if node['time'] > 0:
                if pred_trues > 0:
                    # Edge was previously blocked
                    prob = self.persistence
                else:
                    # Chance for spontaneous blockage
                    prob = 0.001
            else:
                if pred_trues == 0:
                    prob = node['truth_table']['prob_both_no_people']
                elif pred_trues == 1:
                    prob = node['truth_table']['prob_only_u']
                elif pred_trues == 2:
                    prob = node['truth_table']['prob_both_with_people']
                else:
                    print("ERROR! Unexpected number of true predecessors")
                    exit(1)
        if prob < 0:
            print("ERROR! Something went wrong with calculating the probs given parents")
            exit(1)
        if evidence[node_id]:
            return prob
        return 1 - prob

    def probability_path_is_clear(self, path, time, evidence, account_for_travel_time=False):
        node_list = self.path_to_nodes(path, time, account_for_travel_time)
        if node_list == -1:
            return
        p = 1
        for node in node_list:
            p *= self.enumerate_ask(node, evidence)[1]
            evidence[node] = False
        print(p)
        return p

    def path_to_nodes(self, path, time, account_for_travel_time):
        nodes = []
        for i in range(0, len(path) - 1):
            if time > self.curr_time:
                self.advance_time(time - self.curr_time)
            u = path[i]
            v = path[i + 1]
            for n in self.graph.edges(data=True):
                if (n[0] == u and n[1] == v) or (n[0] == v and n[1] == u):
                    eid = n[2]['eid']
                    for sn in self.dbn.nodes(data=True):
                        if sn[1]['type'] == 'is_edge_blocked' and sn[1]['eid'] == eid and sn[1]['time'] == time:
                            nodes.append(sn[0])
                            if account_for_travel_time:
                                time += n[2]['weight']
                            break
        return nodes

    def draw_graph(self):
        for node in self.dbn.nodes(data=True):
            print(node)

    def find_sn_id(self, rep_string):
        parameters = rep_string.lower().split()
        if parameters[0] == 'v':
            return self.find_sn_id_for_vertex(int(parameters[1]))
        else:
            return self.find_sn_id_for_edge(int(parameters[1]), int(parameters[2]))

    def find_sn_id_for_vertex(self, vid):
        for node in self.dbn.nodes(data=True):
            if node[1]['type'] == 'people_in_node' and node[1]['vid'] == vid:
                return node[0]
        return -1

    def find_sn_id_for_edge(self, eid, time):
        if time > self.curr_time:
            self.advance_time(time - self.curr_time)
        for node in self.dbn.nodes(data=True):
            if node[1]['type'] == 'is_edge_blocked' and node[1]['eid'] == eid and node[1]['time'] == time:
                return node[0]
        return -1
