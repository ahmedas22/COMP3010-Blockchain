import socket
import protocol
from chain import Blockchain
import select
import time
import uuid
import json
import uuid
import socket
import select
import time


# def validate(self) -> bool:
#     # Check if the blockchain is not empty
#     if not self.chain:
#         return False
#
#     # Validate the first block separately (genesis block)
#     if not self.chain[0].validate():
#         return False
#
#     # Validate subsequent blocks
#     for i in range(1, len(self.chain)):
#         if not self.chain[i].validate():
#             return False
#
#     return True

class Peer:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name


class GossipProtocol:
    def __init__(self, my_peer):
        self.my_peer = my_peer
        self.peers = set()

    def make_gossip(self):
        j = json.dumps({
            "type": "GOSSIP",
            "host": self.my_peer.host,
            "port": self.my_peer.port,
            "id": str(uuid.uuid4()),
            "name": self.my_peer.name
        })
        return j.encode()

    def make_gossip_reply(self, peer):
        j = json.dumps({
            "type": "GOSSIP_REPLY",
            "host": peer.host,
            "port": peer.port,
            "name": peer.name
        })
        return j.encode()

    def gossip_to_well_known_host(self):
        well_known_host = "192.168.101.248"
        well_known_port = 8999

        gossip_msg = self.make_gossip()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(gossip_msg, (well_known_host, well_known_port))

    def handle_gossip(self, data):
        gossip_data = json.loads(data.decode())

        if gossip_data["id"] not in self.peers:
            self.peers.add(gossip_data["id"])
            reply_msg = self.make_gossip_reply(self.my_peer)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(reply_msg, (gossip_data["host"], gossip_data["port"]))

            # Repeat the message to 3 peers
            for peer_id in list(self.peers)[:3]:
                peer = self.peers[peer_id]
                gossip_msg = self.make_gossip()

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(gossip_msg, (peer.host, peer.port))

    def handle_gossip_reply(self, data):
        reply_data = json.loads(data.decode())
        print(
            f"Received GOSSIP_REPLY from {reply_data['host']}:{reply_data['port']} - {reply_data['name']}")

    def start_gossiping(self):
        while True:
            self.gossip_to_well_known_host()
            self.check_for_messages()

            time.sleep(30)

    def check_for_messages(self):
        host = "192.168.101.248"
        port = self.my_peer.port

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((host, port))
            s.settimeout(5)  # Timeout after 5 seconds

            try:
                data, addr = s.recvfrom(1024)
                if data:
                    self.handle_gossip(data, addr)
            except socket.timeout:
                pass


if __name__ == "__main__":
    my_peer = Peer("192.168.101.248", 8999, "Some name here!")

    gossip_protocol = GossipProtocol(my_peer)
    gossip_protocol.start_gossiping()
    # def gossip(self, gossip_duration=0.5):
    #     start_time = time.time()
    #     end_time = start_time + gossip_duration

    #     # Regular gossiping
    #     while time.time() < end_time:
    #         for peer in self.peers:
    #             if peer.id not in self.ignore_list:
    #                 self.receive_gossip_reply(
    #                     peer, peer.handle_msg(repr(self.my_peer).encode()))

    #         # Repeated gossip to 3 tracked peers
    #         for _ in range(3):
    #             for tracked_peer in self.tracked_peers:
    #                 if tracked_peer.id not in self.ignore_list:
    #                     tracked_peer.send_msg(repr(self.my_peer).encode())
    #                     self.receive_gossip_reply(tracked_peer)

    #         # Receive gossip replies from all peers
    #         new_peers = self.receive_gossip_replies()

    #         # Update peer list with new peers
    #         for new_peer in new_peers:
    #             if new_peer not in self.peers:
    #                 self.peers.append(new_peer)

    # def receive_gossip_reply(self, peer, msg):
    #     if msg and json.loads(msg)["type"] == "GOSSIP_REPLY":
    #         gossip_reply = json.loads(msg)
    #         new_peer = Peer(
    #             gossip_reply["name"], gossip_reply["host"], gossip_reply["port"])

    #         if new_peer not in self.peers:
    #             self.peers.append(new_peer)

    # def receive_gossip_replies(self):
    #     new_peers = []
    #     for peer in self.peers:
    #         msg, addr = peer.receive_msg()
    #         if msg and json.loads(msg)["type"] == "GOSSIP_REPLY":
    #             self.receive_gossip_reply(peer)
    #             new_peers.append(Peer(json.loads(msg)["name"], json.loads(msg)[
    #                              "host"], json.loads(msg)["port"]))
    #     return new_peers
