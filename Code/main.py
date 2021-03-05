from simulator import Simulator


def main():
    # reader = GraphReader()
    # graph, persistence = reader.read('test.txt')
    # builder = DBNBuilder(graph, persistence)
    # builder.create_dbn()
    # builder.advance_time()
    # builder.print_network_structure()
    # # print(builder.enumerate_ask(1, {2: True}))
    # builder.probability_path_is_clear([0, 1, 2], 0, {1: True}, True)
    sim = Simulator()
    sim.interface()


if __name__ == '__main__':
    main()
