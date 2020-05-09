from dataclasses import dataclass

# should we use dataclasses?
# todo find a way to use list<type> in data class type
from model.torrent_file import TorrentFile


@dataclass
class MetaInfoFile:
    announce: str
    info: TorrentFile  # list of TorrentFile
    announce_list: list = None  # list of string
    comment: str = None
    created_by: str = None
    creation_date: str = None
