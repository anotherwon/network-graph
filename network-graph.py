#!/usr/bin/python3

import fileinput
import io
import json
import sys
from graphviz import Digraph


class NetworkInterface:
    def __init__(self, data):
        self.index = data['ifindex']
        self.name = data['ifname']

        self.state = data['operstate']
        if self.state == 'UNKNOWN' and 'UP' in data['flags']:
            self.state = 'UP'

        self.master = None
        if 'master' in data:
            self.master = data['master']

        self.link = None
        if 'link' in data:
            self.link = data['link']

        self.link_index = None
        if 'link_index' in data:
            self.link_index = data['link_index']

        self.link_netnsid = None
        if 'link_netnsid' in data:
            self.link_netnsid = data['link_netnsid']

        self.type = None
        if 'linkinfo' in data and 'info_kind' in data['linkinfo']:
            self.type = data['linkinfo']['info_kind']
            if self.type == 'tun':
                self.type = data['linkinfo']['info_data']['type']

        self.addresses = []
        if 'addr_info' in data:
            for address in data['addr_info']:
                self.addresses.append(str(address['local']) + "/" + str(address['prefixlen']))

    def __str__(self):
        return str(self.index) + ": " + self.name

    def get_label(self):
        result = ['<']
        result.append(f'<b><font color="{self.get_color()}">{self.name}</font></b>')
        if self.type is not None:
            result.append(f'<br/>type: {self.type}')
        if len(self.addresses) > 0:
            result.append('<br/>')
            for address in self.addresses:
                result.append(f'<br/>{address}')
        result.append('>')
        return ''.join(result)

    def get_color(self):
        color = {
            'UP': 'green3',
            'DOWN': 'red',
            'UNKNOWN': 'yellow3'
        }
        return color.get(self.state, 'black')


class NetworkNamespace:
    def __init__(self, name):
        self.name = name
        self.id = None
        self.interfaces = []
        self.mapping = {}

    def __str__(self):
        return 'namespace: ' + self.name

    def set_id(self, id):
        self.id = id

    def add_interface(self, interface):
        self.interfaces.append(interface)

    def add_ns_mapping(self, data):
        if 'name' not in data:
            data['name'] = ''
        self.mapping.update({data['nsid']: data['name']})

    def get_interface_index(self, name):
        for interface in self.interfaces:
            if interface.name == name:
                return interface.index
        return None

    def get_nsname(self, nsid):
        return self.mapping.get(nsid)


def main():
    if len(sys.argv) == 1:
        infile = sys.stdin
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'r')
    else:
        sys.exit('usage')

    namespaces = {}
    nsname = ''
    namespaces[nsname] = NetworkNamespace(nsname)
    for line in infile:
        if line.startswith('['):
            data = json.loads(line)
            for item in data:
                if 'ifindex' in item:
                    namespaces[nsname].add_interface(NetworkInterface(item))
                elif 'nsid' in item:
                    namespaces[nsname].add_ns_mapping(item)
        elif line.startswith('netns:'):
            nsname = line.split()[1]
            namespaces[nsname] = NetworkNamespace(nsname)

    dot = Digraph('network')
    dot.graph_attr['labeljust'] = 'l'
    dot.graph_attr['labelloc'] = 'b'
    dot.node_attr['shape'] = 'hexagon'

    for namespace in namespaces.values():
        with dot.subgraph(name='cluster_' + namespace.name) as c:
            if len(namespace.name) > 0:
                c.attr(label='netns: ' + namespace.name)
            c.attr(margin='16')
            for interface in namespace.interfaces:
                node_prefix = 'node_' + namespace.name + '_'
                node_name = node_prefix + str(interface.index)
                c.node(node_name, interface.get_label())

                if interface.master is not None:
                    master_index = namespace.get_interface_index(interface.master)
                    if master_index is None:
                        sys.exit("master index for %s not found!".format(interface.master))
                    c.edge(node_prefix + str(master_index), node_name)

                if interface.link is not None:
                    link_index = namespace.get_interface_index(interface.link)
                    if link_index is None:
                        sys.exit("link index for %s not found!".format(interface.link))
                    c.edge(node_name, node_prefix + str(link_index), constraint='false', style='dashed')

    for namespace in namespaces.values():
        for interface in namespace.interfaces:
            node_prefix = 'node_' + namespace.name + '_'
            node_name = node_prefix + str(interface.index)
            if interface.link_index is not None and interface.link_netnsid is not None:
                link_nsname = namespace.get_nsname(interface.link_netnsid)
                remote_node_name = 'node_' + link_nsname + '_' + str(interface.link_index)
                dot.edge(node_name, remote_node_name, constraint='false', style='dashed')

    print(dot.source)
    dot.format = 'x11'
    dot.render()


if __name__ == '__main__':
    main()
