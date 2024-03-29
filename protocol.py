# -----------------------------------------
# NAME: Ahmed Hasan
# STUDENT NUMBER: 7932883
# COURSE: COMP 3010, SECTION: A01
# INSTRUCTOR: Robert Guderian
# ASSIGNMENT: assignment 3
# PORTS ASSIGNED: 8790-8794
# Classes: Config and Protocol
#
# -----------------------------------------


import argparse
import json
import socket
import uuid
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from peer import Peer


class Config:
    # Argument Parser
    parser = argparse.ArgumentParser(description='Peer Configurator.')
    parser.add_argument('ip', nargs='?', default=None, help='IP address to process')
    parser.add_argument('port', type=int, nargs='?', default=None, help='Port number to use')
    args = parser.parse_args()

    # Host
    if args.ip:
        HOST = args.ip
        FAMOUS_HOST = HOST
    else:
        HOST = socket.gethostbyname(socket.gethostname())
        FAMOUS_HOST = "silicon.cs.umanitoba.ca"

    # Port
    FAMOUS_PORT = 8999
    if args.port:
        PORT = args.port
    else:
        PORT = 8793

    # Name
    NAME = "Ahmed^2"
    FAMOUS_NAME = "Famous_Peer"

    # Peers
    my_peer = None
    famous_peer1 = None

    # Constraints
    MAX_MESSAGES = 10
    MAX_CHARS = 20
    NONCE_MAX_CHARS = 40
    DIFFICULTY = 8

    # Timeouts
    GOSSIP_TIMEOUT = 1.5
    CONSENSUS_TIMEOUT = GOSSIP_TIMEOUT * 4
    STAT_TIMEOUT = GOSSIP_TIMEOUT * 2
    GOSSIP_INTERVAL = 30
    MINING_INTERVAL = GOSSIP_INTERVAL * 4
    CLEANUP_INTERVAL = GOSSIP_INTERVAL + STAT_TIMEOUT
    CONSENSUS_INTERVAL = 300
    MAX_TRACKED_PEERS = 3

    # Socket
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_socket.bind(("", PORT))
    recv_socket.settimeout(GOSSIP_TIMEOUT)
    consensus_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    consensus_socket.settimeout(GOSSIP_TIMEOUT)

    # Words
    word_list = ["hello", "world", "i love rob", "3010 is hard", "3010 is awesome", "bahrain", "apple", "banana",
                 "cherry", "orange", "grape", "kiwi", "melon", "pear", "plum", "strawberry"]


class Protocol:

    @staticmethod
    def parse_msg(msg: bytes) -> dict:
        try:
            return json.loads(msg.decode())
        except json.JSONDecodeError:
            Protocol.handle_json_error()

    @staticmethod
    def encode_dict(data: Union[dict, str]) -> Union[str, dict]:
        try:
            return json.dumps(data)
        except json.JSONDecodeError:
            Protocol.handle_json_error()

    @staticmethod
    def make_gossip(peer: 'Peer') -> str:
        j = json.dumps({
            "type": "GOSSIP",
            "host": peer.host,
            "port": peer.port,
            "id": str(uuid.uuid4()),
            "name": peer.name
        })
        return j

    @staticmethod
    def make_gossip_reply(peer: 'Peer') -> str:
        j = json.dumps({
            "type": "GOSSIP_REPLY",
            "host": peer.host,
            "port": peer.port,
            "name": peer.name
        })
        return j

    @staticmethod
    def make_get_block(height: int, consensus: bool = False) -> str:
        j = {
            "type": "GET_BLOCK",
            "height": height
        }
        if consensus:
            j["consensus"] = True
        return json.dumps(j)

    @staticmethod
    def make_get_block_reply(timestamp: int, hash: str, miner: str = None, nonce: str = None, height: int = None,
                             messages: list = None) -> str:
        j = json.dumps({
            "type": "GET_BLOCK_REPLY",
            "hash": hash,
            "height": height,
            "messages": messages,
            "minedBy": miner,
            "nonce": nonce,
            "timestamp": timestamp
        })
        return j

    @staticmethod
    def make_announce(height: int, miner: str, nonce: str, messages: list, block_hash: str, timestamp: int) -> str:
        j = json.dumps({
            "type": "ANNOUNCE",
            "height": height,
            "minedBy": miner,
            "nonce": nonce,
            "messages": messages,
            "hash": block_hash,
            "timestamp": timestamp
        })
        return j

    @staticmethod
    def make_stats(consensus: bool = False) -> str:
        j = {
            "type": "STATS"
        }
        if consensus:
            j["consensus"] = True

        return json.dumps(j)

    @staticmethod
    def make_stats_reply(height: int, block_hash: str) -> str:
        j = json.dumps({
            "type": "STATS_REPLY",
            "height": height,
            "hash": block_hash
        })
        return j

    @staticmethod
    def make_consensus() -> str:
        j = json.dumps({
            "type": "CONSENSUS"
        })
        return j

    @staticmethod
    def handle_json_error():
        print("Invalid JSON format in the received data.")
        return {"type": "JSON ERROR"}
