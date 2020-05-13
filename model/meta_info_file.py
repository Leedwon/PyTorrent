from dataclasses import dataclass

from model.torrent_file import TorrentFile


# should we use dataclasses?
# todo find a way to use list<type> in data class type

@dataclass
class MetaInfoFile:
    announce: str
    info_hash: bytes
    torrent_file: TorrentFile
    announce_list: list = None  # list of string
    comment: str = None
    created_by: str = None
    creation_date: str = None
