import select
import time
import threading
from chain import Block, Blockchain
from peer import Peer, Gossiper
from protocol import Protocol, Config


class PeerList:
    def __init__(self):
        self.peers = []

        self.tracked_peers = []

        self.chains = []
        self.chosen_chain = {}
        self.ignore = []
        self.sender = None
        self.in_consensus = False
        self.failed_consensus = False
        self.chains_lock = threading.Lock()  # Lock for access to self.chains
        self.chain_lock = threading.Lock()  # Lock for access to self.chains
        self.ignore_lock = threading.Lock()  # Lock for access to self.chains
        self.chosen_chain_lock = threading.Lock()  # Lock for access to self.chosen_chain

        self.gossiper = Gossiper()
        self.chain = Blockchain()

    # Peer Stats
    def handle_stats(self, message: dict, sender_addr: tuple, socket) -> None:
        if not message.get("consensus"):
            with self.chain_lock:
                reply_msg = str(self.chain)
        else:
            reply_msg = Protocol.make_stats()
        Peer.send_msg(reply_msg, sender_addr, socket)

    def handle_stats_reply(self, message: dict, sender_addr: tuple) -> None:
        if message:
            height = int(message.get("height"))
            block_hash = message.get("hash")
            if height and block_hash:
                with self.chains_lock:
                    self.chains.append({sender_addr: {"height": height, "hash": block_hash}})

    def request_peer_stats(self) -> None:
        stats_recv_thread = threading.Thread(target=Peer.recv_msg, args=(Config.con_socket, self), daemon=True)
        stats_recv_thread.start()
        for peer in self.peers:
            if peer.get_addr() not in self.ignore:
                self.handle_msg(Protocol.parse_msg(Protocol.make_stats(True).encode()), peer.get_addr(),
                                Config.con_socket)
        stats_recv_thread.join(Config.STAT_TIMEOUT)

    # Blocks
    def handle_get_block(self, message: dict, sender_addr: tuple, socket) -> None:
        height = message.get("height")
        if not message.get("consensus"):
            if not height or height >= self.chain.height:
                block = Block()
            else:
                block = self.chain[height]
            reply_msg = Protocol.make_get_block_reply(block.timestamp, block.hash, block.miner, block.nonce,
                                                      block.height, block.messages)
        else:
            reply_msg = Protocol.make_get_block(height)
        Peer.send_msg(reply_msg, sender_addr, socket)

    def handle_get_block_reply(self, message: dict) -> None:
        new_block = Block(message.get("hash"), message.get("minedBy"), message.get("height"),
                          message.get("messages"), message.get("nonce"), message.get("timestamp"))
        with self.chosen_chain_lock:
            self.chosen_chain[message.get("height")] = new_block

    def get_chain_blocks(self, chain) -> None:
        chain_recv_thread = threading.Thread(target=Peer.recv_msg, args=(Config.con_socket, self), daemon=True)
        chain_recv_thread.start()
        for _, value in chain.items():
            chain_height = value.get("height")
            for height in range(chain_height - 1, self.chain.height - 1, -1):
                if height not in self.chosen_chain or self.chosen_chain[height] is None:
                    with self.chains_lock:
                        self.sender = self.tracked_peers.pop(0)
                        self.tracked_peers.append(self.sender)
                        self.handle_msg(Protocol.parse_msg(Protocol.make_get_block(height, True).encode()), self.sender,
                                        Config.con_socket)
        chain_recv_thread.join(Config.CONSENSUS_TIMEOUT)

    def is_missing_blocks(self, chain):
        for _, value in chain.items():
            chain_height = value.get("height")
            for height in range(chain_height - 1, self.chain.height - 1, -1):
                if height not in self.chosen_chain or self.chosen_chain[height] is None:
                    return True
            return False

    def add_blocks_to_blockchain(self) -> bool:
        added = False
        for index, block in sorted(self.chosen_chain.items()):
            added = self.chain.add_block(block)
            if not added:
                break
        return added

    def handle_msg(self, message: dict, sender_addr: tuple, socket=Config.recv_socket) -> None:
        if message:
            msg_type = message.get("type")

            match msg_type:
                case "GOSSIP":
                    self.gossiper.handle_gossip(self.peers, message, sender_addr)
                case "GOSSIP_REPLY":
                    self.gossiper.handle_gossip_reply(self.peers, message)
                case "STATS":
                    self.handle_stats(message, sender_addr, socket)
                case "STATS_REPLY":
                    self.handle_stats_reply(message, sender_addr)
                case "CONSENSUS":
                    if not self.in_consensus:
                        self.consensus()
                case "GET_BLOCK":
                    self.handle_get_block(message, sender_addr, socket)
                case "GET_BLOCK_REPLY":
                    self.handle_get_block_reply(message)
                case _:
                    print("Not implemented")

    def consensus(self) -> None:
        try:
            self.in_consensus = True
            self.chains = []
            self.tracked_peers = []
            self.sender = None
            print("STARTING CONSENSUS")

            # Step 1: Get stats from peers
            self.request_peer_stats()

            # Step 2: Pick peers with the longest chains
            majority_chains = self.choose_majority_chain()
            chosen_chain_index = 0

            for chosen_chain_index in range(len(majority_chains)):
                chain = majority_chains[chosen_chain_index]
                self.chosen_chain = {}
                # Step 2.a: Get blocks in the chosen chain
                self.get_chain_blocks(chain)

                # Step 2.b: if missing blocks, re-request them
                retries = 0
                while self.is_missing_blocks(chain) and retries <= 3:
                    self.get_chain_blocks(chain)
                    retries += 1

                # Step 3: if not missing blocks, finish consensus
                if not self.is_missing_blocks(chain):
                    # Step 3.a: add blocks to blockchain
                    added = self.add_blocks_to_blockchain()

                    # Step 3.b: if chain is valid
                    if added and self.chain.validate():
                        print("CONSENSUS COMPLETED")
                        with self.ignore_lock:
                            self.ignore = []
                            return
            # Step 4: if all indexes were tried, we re-do consensus
            if 0 < len(majority_chains) >= (chosen_chain_index + 1):
                for sender in self.tracked_peers:
                    with self.ignore_lock:
                        self.ignore.append(sender)
                re_consensus_thread = threading.Thread(target=self.consensus, daemon=True)
                re_consensus_thread.start()
                re_consensus_thread.join()
        except Exception as e:
            print(f"Error in consensus: {e}")
        finally:
            self.in_consensus = False

    def choose_majority_chain(self) -> list:
        max_height = 0
        longest_chains = []

        # Find the maximum height among the consensus data
        for chain in self.chains:
            for key, value in chain.items():
                height = value.get("height")
                top_hash = value.get("hash")

                if height > max_height:
                    max_height = height
                    longest_chains = [chain]
                elif height == max_height:
                    for _, value2 in longest_chains[0].items():
                        if top_hash == value2.get("hash"):
                            longest_chains.append(chain)

        for longest_chain in longest_chains:
            for key, _ in longest_chain.items():
                self.tracked_peers.append(key)

        return longest_chains


if __name__ == "__main__":
    Config.my_peer = Peer(Config.NAME, Config.HOST, Config.PORT)
    Config.famous_peer1 = Peer(Config.FAMOUS_NAME, Config.FAMOUS_HOST, Config.FAMOUS_PORT)
    peers = PeerList()
    consensus_thread = None
    threads = []

    try:
        last_gossip_time = 0
        last_consensus_time = 0
        peers.gossiper.join_network(Config.famous_peer1)

        while True:
            current_time = time.time()
            readable, _, _ = select.select([Config.recv_socket], [], [], 0.1)

            for sock in readable:
                Peer.recv_msg(sock, peers)

            if current_time >= last_gossip_time + Config.GOSSIP_INTERVAL:
                peers.gossiper.gossip_to_peers(peers.peers, Protocol.parse_msg(repr(Config.my_peer).encode()))
                last_gossip_time = current_time

            if time.time() >= last_consensus_time + Config.CONSENSUS_INTERVAL:
                last_consensus_time = time.time()

                if not peers.in_consensus:
                    consensus_thread = threading.Thread(target=peers.consensus, daemon=True)
                    consensus_thread.start()

            if consensus_thread and not consensus_thread.is_alive():
                consensus_thread.join()
                consensus_thread = None

    except KeyboardInterrupt:
        print("Peer shutting down.")
        for thread in threads:
            thread.join()
