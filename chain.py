import hashlib
import time

from protocol import Protocol, Config


class Block:
    def __init__(self, hash: str = None, miner: str = None, height: int = None, messages: list = None,
                 nonce: str = None, timestamp: str = None) -> None:
        if messages:
            self.messages = messages
        else:
            self.messages = []
        self.hash = hash
        self.height = height
        self.miner = miner
        if timestamp is not None:
            self.timestamp = int(timestamp)
        else:
            self.timestamp = int(time.time())
        self.nonce = nonce

    def calculate_hash(self) -> str:
        base_hash = hashlib.sha256()
        offset = None

        if self.height and not self.height == 0:
            prev_hash = Blockchain.chain[self.height - 1].hash
            base_hash.update(prev_hash.encode())

        if self.miner:
            base_hash.update(self.miner.encode())

        for message in self.messages:
            base_hash.update(message.encode())

        base_hash.update(self.timestamp.to_bytes(8, 'big'))

        if self.nonce:
            base_hash.update(self.nonce.encode())

        return base_hash.hexdigest()[:offset]

    def validate(self, difficulty) -> bool:
        if len(self.messages) > Config.MAX_MESSAGES:
            return False

        for message in self.messages:
            if len(message) > Config.MAX_CHARS:
                return False

        if self.nonce and len(self.nonce) > Config.NONCE_MAX_CHARS:
            return False

        to_add_hash = self.calculate_hash()

        if Blockchain.calculate_difficulty(to_add_hash) < difficulty:
            for offset in range(difficulty, Config.DIFFICULTY-1, -1):
                if to_add_hash[-1 * (difficulty-offset):] == '0' * (difficulty-offset) and Blockchain.height > 1:
                    return True

        if to_add_hash[-1 * difficulty:] != '0' * difficulty:
            return False

        return True

    def mine_block(self, difficulty):
        current_hash = self.calculate_hash()

        while not current_hash.endswith("0" * difficulty):
            self.nonce += "1"
            current_hash = self.calculate_hash()

        return current_hash


class Blockchain:
    chain = []
    height = 0
    difficulty = Config.DIFFICULTY

    @classmethod
    def add_block(cls, to_add: 'Block') -> bool:
        out = False

        if to_add not in cls.chain and to_add.validate(cls.difficulty):
            cls.chain.append(to_add)
            cls.difficulty = cls.calculate_difficulty(to_add.hash)
            cls.height += 1
            out = True

        return out

    @staticmethod
    def calculate_difficulty(hash):
        difficulty = 0
        if hash is not None:
            for char in reversed(hash):
                if char == '0':
                    difficulty += 1
                else:
                    break
        return difficulty
    @classmethod
    def validate(cls):
        for i in range(1, len(cls.chain)):
            current_block = cls.chain[i]
            prev_block = cls.chain[i - 1]

            if not current_block.validate(cls.difficulty) or current_block.hash == prev_block.hash:
                cls.chain[i:] = []
                cls.height = i
                return False

        return True

    @classmethod
    def get_last_block(cls) -> str:
        if cls.height > 0:
            return cls.chain[-1].hash
        else:
            return Block().calculate_hash()

    @classmethod
    def __eq__(cls, other):
        if isinstance(other, int):
            return cls.height == other
        else:
            return NotImplemented

    @classmethod
    def __getitem__(cls, height):
        return cls.chain[height]

    @classmethod
    def __str__(cls):
        return Protocol.make_stats_reply(cls.height, cls.get_last_block())
