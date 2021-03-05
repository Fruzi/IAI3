from dbn_builder import DBNBuilder
from graph_reader import GraphReader


class Simulator:
    def __init__(self):
        reader = GraphReader()
        print('insert path to graph file:')
        path = 'test.txt'  # path = input().replace('"', '')1
        self.graph, persistence = reader.read(path)
        self.builder = DBNBuilder(self.graph, persistence)
        self.builder.create_dbn()
        self.evidence = {}
        self.human_evidence = {}

    def interface(self):
        while True:
            print('1. Add evidence')
            print('2. Reset evidence')
            print('3. Show evidence')
            print('4. Query vertex')
            print('5. Query edge')
            print('6. Query path')
            print('7. Quit')
            i = int(input('Type action index: '))
            if i == 1:
                self.add_evidence()
            elif i == 2:
                self.reset_evidence()
            elif i == 3:
                self.show_evidence()
            elif i == 4:
                self.query_vertex()
            elif i == 5:
                self.query_edge()
            elif i == 6:
                self.query_path()
            else:
                break
            print()

    def add_evidence(self):
        print('Enter evidence in the form: v id t/f or e id t t/f')
        sevidence = input().lower()
        snid = self.builder.find_sn_id(sevidence)
        self.evidence[snid] = (sevidence[-1] == 't')
        self.human_evidence[sevidence[:-2]] = (sevidence[-1] == 't')

    def reset_evidence(self):
        self.evidence.clear()
        self.human_evidence.clear()

    def show_evidence(self):
        if self.human_evidence:
            for piece in self.human_evidence:
                print(f'{piece} {self.human_evidence[piece]}')
        else:
            print("no evidence found")

    def query_vertex(self):
        vid = int(input("Enter vid: "))
        snid = self.builder.find_sn_id_for_vertex(vid)
        print(self.builder.enumerate_ask(snid, self.evidence.copy()))

    def query_edge(self):
        eid = int(input("Enter eid: "))
        time = int(input("Enter time: "))
        snid = self.builder.find_sn_id_for_edge(eid, time)
        print(self.builder.enumerate_ask(snid, self.evidence.copy()))

    def query_path(self):
        time = int(input("Enter starting time: "))
        print("Enter vertices id in path separated by space")
        path = [int(i) for i in input().split()]
        self.builder.probability_path_is_clear(path,time,self.evidence.copy(),True)
