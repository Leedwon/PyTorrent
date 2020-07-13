from dataclasses import dataclass


@dataclass
class Peer:
    peer_id: str
    ip: str
    port: int
