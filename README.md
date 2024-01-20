# Assignment 3 

## Getting Started

To start your peer, follow these steps:

1. Open a terminal.
2.  Run the following command:

```bash
python main.py [arguments]
```

### Command Line Arguments

- `[ip]`: optional ip address in format `192.168.y.x` for host, by default it's `silicon.cs.umanitoba.ca`
- `[port]`: optional port number, by default it's `8793`
- ...

### Synchronization

The synchronization process may take approximately `1.5` minutes. During synchronization, you can expect to see on the terminal, all the blocks, gossips and stats that have been requested or responded to.

## Consensus Code

The consensus code for choosing which chain to synchronize is located in the file `main.py` at lines `202-224`. It picks chains by doing the following:

- iterating through the `chains` list, which contains stats of all peers that answered before timeout. 
- It identifies the chain with the maximum height (`max_height`) 
	-  In the case of a tie, it appends all chains with the same height and matching top hash to the `longest_chains` list.
-  It updates the list of tracked peers (`tracked_peers`) based on the chosen longest chains and returns the list of longest chains.

## Cleaning up Peers

The cleanup process for peers can be found in the file `main.py` at lines `262-266, 113-116`. It cleans up peers by doing the following:

-	Every peer has an instance variable of `last_message_time` that keeps track of the last time a message was received
	-	`last_message_time` changes every time `handle_msg` is called since it holds tuple of an address which I find the peer associated with, by calling `find_peer_by_addr`  
-	The peers finally get cleaned up by comparing every peer's `last_message_time` to `current_time`  with the constant `CLEANUP_INTERVAL` added to `last_message_time` which is false, it kicks out that peer from the peer list  

