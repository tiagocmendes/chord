# coding: utf-8

import socket
import threading
import logging
import pickle
from utils import dht_hash, contains_predecessor, contains_successor


class DHT_Node(threading.Thread):
    def __init__(self, address, dht_address=None, timeout=3):
        threading.Thread.__init__(self)
        self.id = dht_hash(address.__str__())
        self.addr = address
        self.dht_address = dht_address

        # finger table dictionary
        self.finger_table = {}

        # method: 'FINGER' ttl - 9
        # method: 'FINGER' -> volta ao anel

        if dht_address is None:
            # put successor node in the FT
            self.finger_update(self.id, address)
            self.predecessor_id = None
            self.predecessor_addr = None
            self.inside_dht = True
        else:
            self.inside_dht = False
            self.successor_id = None
            self.successor_addr = None
            self.predecessor_id = None
            self.predecessor_addr = None
        self.keystore = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.logger = logging.getLogger("Node {}".format(self.id))
    
    # add a node to the FT
    def finger_update(self, id, addr):
        self.finger_table[id] = addr
    
    # get successor node
    def finger_get(self, key_hash):
        if self.id < key_hash <= list(self.finger_table.keys())[0]:
            return 0
        elif list(self.finger_table.keys())[0] < self.id:
            if self.id < key_hash <= 1024:
                return 0
        elif list(self.finger_table.keys())[0] < key_hash or key_hash <= self.id:
            keys = sorted(self.finger_table)
            for i in range(len(keys)-1, -1, -1):
                if keys[i] <= key_hash:
                    if keys[i] < self.id:
                        return self.finger_table[keys[i+1]]
                    return self.finger_table[keys[i]]
        else:
            return -1
        

    def send(self, address, o):
        p = pickle.dumps(o)
        self.socket.sendto(p, address)

    def recv(self):
        try:
            p, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None
        else:
            if len(p) == 0:
                return None, addr
            else:
                return p, addr

    def node_join(self, args):
        self.logger.debug('Node join: %s', args)
        addr = args['addr']
        identification = args['id']
        if self.id == list(self.finger_table.keys())[0]:
            self.finger_table[identification] = addr
            args = {'successor_id': self.id, 'successor_addr': self.addr}
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
        elif contains_successor(self.id, self.successor_id, identification):
            args = {'successor_id': self.successor_id, 'successor_addr': self.successor_addr}
            self.successor_id = identification
            self.successor_addr = addr
            self.finger_table[identification] = add
        else:
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
            self.logger.debug('Find Successor(%d)', args['id'])
            self.send(self.successor_addr, {'method': 'JOIN_REQ', 'args':args})
        self.logger.info(self)

    def notify(self, args):
        self.logger.debug('Notify: %s', args)
        if self.predecessor_id is None or contains_predecessor(self.id, self.predecessor_id, args['predecessor_id']):
            self.predecessor_id = args['predecessor_id']
            self.predecessor_addr = args['predecessor_addr']
        self.logger.info(self)

    def stabilize(self, x, addr):
        self.logger.debug('Stabilize: %s %s', x, addr)
        if x is not None and contains_successor(self.id, self.successor_id, x):
            self.successor_id = x
            self.successor_addr = addr
        args = {'predecessor_id': self.id, 'predecessor_addr': self.addr}
        self.send(self.successor_addr, {'method': 'NOTIFY', 'args':args})

    def put(self, key, value, address):
        key_hash = dht_hash(key)
        self.logger.debug('Put: %s %s', key, key_hash)

        succ_addr = self.finger_get(key_hash)
        if succ_addr == -1:
            self.send(address, {'method': 'NACK'})
        elif succ_addr == 0:
            self.keystore[key] = value
            self.send(address, {'method': 'ACK'})
        else:
            self.send(succ_addr, {'method': 'PUT', 'args':{'key': key, 'value': value, 'client_addr': address}})


    def get(self, key, address):
        key_hash = dht_hash(key)
        self.logger.debug('Get: %s %s', key, key_hash)
        
        succ_addr = finger_get(key_hash)
        if succ_addr == -1:
            self.send(address, {'method': 'NACK'})
        elif succ_addr == 0:
            value = self.keystore[key]
            self.send(address, {'method': 'ACK', 'args': value})
        else:
            self.send(succ_addr, {'method': 'GET', 'args': {'key': key, 'client_addr': address}})

    def run(self):
        self.socket.bind(self.addr)

        while not self.inside_dht:
            o = {'method': 'JOIN_REQ', 'args': {'addr':self.addr, 'id':self.id}}
            self.send(self.dht_address, o)
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                self.logger.debug('O: %s', o)
                if o['method'] == 'JOIN_REP':
                    args = o['args']
                    self.successor_id = args['successor_id']
                    self.successor_addr = args['successor_addr']
                    self.inside_dht = True
                    self.logger.info(self)

        done = False
        while not done:
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                self.logger.info('O: %s', o)
                if o['method'] == 'JOIN_REQ':
                    self.node_join(o['args'])
                elif o['method'] == 'NOTIFY':
                    self.notify(o['args'])
                elif o['method'] == 'PUT':
                    if 'client_addr' in o['args']:
                        self.put(o['args']['key'], o['args']['value'], o['args']['client_addr'])
                    else:
                        self.put(o['args']['key'], o['args']['value'], addr)
                elif o['method'] == 'GET':
                    if 'client_addr' in o['args']:
                        self.get(o['args']['key'], o['args']['client_addr'])
                    else:
                        self.get(o['args']['key'], addr)
                elif o['method'] == 'PREDECESSOR':
                    self.send(addr, {'method': 'STABILIZE', 'args': self.predecessor_id})
                elif o['method'] == 'STABILIZE':
                    self.stabilize(o['args'], addr)
            else:
                # Ask for predecessor to start the stabilize process
                self.send(self.successor_addr, {'method': 'PREDECESSOR'})

    def __str__(self):
        return 'Node ID: {}; DHT: {}; Successor: {}; Predecessor: {}'\
            .format(self.id, self.inside_dht, self.successor_id, self.predecessor_id)

    def __repr__(self):
        return self.__str__()