from dataclasses import dataclass

# should we use inheritance here or composition over inheritance?
# mb there is a better way to represent both single and multi file torrent?
# todo refactor naming convention

@dataclass
class TorrentFile:
    name: str
    piece_length: int
    piece_hashes: list


@dataclass
class SingleFileTorrent(TorrentFile):
    length: int
    md5sum: str = None  # optional


@dataclass
class FileFromMultiFileTorrent:
    length: int
    path: str
    md5sum: str = None  # optional


@dataclass
class MultiFileTorrent(TorrentFile):
    files: list  # list of FileFromMultiFileTorrent
