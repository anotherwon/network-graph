# network-graph

Creates a graph of all network interfaces and their relationships. Supports network namespaces.

## Dependencies
  * iproute2
  * python3
  * python3-graphviz
  * graphviz

## Usage
    sudo ./network-dump.sh > network.json
    ./network-graph.py network.json > network.gv
    dot -Tpng network.gv > network.png

Or all in one:

    sudo ./network-dump.sh | network-graph.py | dot -Tx11


## TODO
  * captions for edges
  * cgroups support
