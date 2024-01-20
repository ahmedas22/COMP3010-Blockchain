# -----------------------------------------
# NAME: Ahmed Hasan
# STUDENT NUMBER: 7932883
# COURSE: COMP 3010, SECTION: A01
# INSTRUCTOR: Robert Guderian
# ASSIGNMENT: assignment 3
# PORTS ASSIGNED: 8790-8794
# Classes: Peer and Gossiper
#
# -----------------------------------------


import random
import uuid
import time

from protocol import Config, Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import PeerList


class Peer:
    def __init__(self, name: str, host: str, port: int, peer_id: str = None):
        self.id = peer_id
        self.name = name
        self.host = host
        self.port = port
        self.last_message_time = int(time.time())  # Initialize with current time

    def get_addr(self):
        addr = (self.host, self.port)
        return addr

    @classmethod
    def send_msg(cls, msg: str, recipient_addr: tuple, sock=Config.recv_socket):
        print(f'To ${recipient_addr}:\n${msg}\n')
        sock.sendto(msg.encode(), recipient_addr)

    @classmethod
    def init_from_gossip(cls, msg: dict) -> 'Peer':
        return cls(msg.get("name"), msg.get("host"), msg.get("port"), msg.get("peer_id", None))

    @classmethod
    def recv_msg(cls, sock, peer_list: 'PeerList') -> None:
        import socket
        try:
            while True:
                msg, addr = sock.recvfrom(1024)
                parsed_msg = Protocol.parse_msg(msg)
                print(f'From ${addr}:\n${parsed_msg}\n')
                peer_list.handle_msg(parsed_msg, addr)
        except socket.timeout:
            return

    def __eq__(self, other):
        out = False
        if isinstance(other, Peer):
            out = self.port == other.port and self.port == other.port and self.name == other.name
            if not self.id:
                self.id = str(uuid.uuid4())
        return out

    def __str__(self):
        return Protocol.make_gossip_reply(self)

    def __repr__(self):
        return Protocol.make_gossip(self)


class Gossiper:

    def __init__(self):
        self.ignore = set()

    def join_network(self, famous_peer: Peer):
        gossip_msg = repr(Config.my_peer)
        famous_peer_addr = famous_peer.get_addr()
        Peer.send_msg(gossip_msg, famous_peer_addr)
        self.ignore.add(Protocol.parse_msg(gossip_msg.encode()).get("id"))

    def handle_gossip(self, peer_list: list, message: dict, sender_addr: tuple) -> None:
        if message.get("id") not in self.ignore:
            self.ignore.add(message.get("id"))

            reply_msg = str(Config.my_peer)
            Peer.send_msg(reply_msg, sender_addr)
            self.gossip_to_peers(peer_list, message)

    def gossip_to_peers(self, peer_list: list, og_msg: dict) -> None:
        # Get three random peers from the list
        random_peers = random.sample(peer_list, min(Config.MAX_TRACKED_PEERS, len(peer_list)))

        # Forward the original gossip message to each random peer
        for peer in random_peers:
            if peer.id != og_msg.get("id"):
                peer_address = (og_msg.get("host"), og_msg.get("port"))
                Peer.send_msg(Protocol.encode_dict(
                    og_msg), peer_address)
                self.ignore.add(og_msg.get("id"))

    @staticmethod
    def handle_gossip_reply(peer_list: list, message: dict) -> None:
        new_peer = Peer.init_from_gossip(message)
        if new_peer not in peer_list:
            peer_list.append(new_peer)
