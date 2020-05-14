import bencoder
import io
import hashlib

from model.meta_info_file import MetaInfoFile
from model.torrent_file import *
from utils.byteswrap import wrap


# todo put to some package
# todo put keys into some consts?
class TorrentFileReader:
    @staticmethod
    def read_file(file_path) -> MetaInfoFile:
        with io.open(file_path, 'rb') as torrent_file:
            decoded = bencoder.decode(torrent_file.read())

            # announce and info must be present thus we don't check for their existence
            announce = decoded[b'announce']
            info = decoded[b'info']

            announce_list = None
            comment = None
            created_by = None
            creation_date = None

            if b'announce-list' in decoded:
                announce_list = decoded[b'announce-list']
            if b'comment' in decoded:
                comment = decoded[b'comment']
            if b'created by' in decoded:
                created_by = decoded[b'created by']
            if b'creation date' in decoded:
                creation_date = decoded[b'creation date']

            if b'files' in info:
                print("multi_file torrent")  # todo move to debug mode only

                return MetaInfoFile(
                    announce=announce,
                    info_hash=TorrentFileReader.create_info_hash(info),
                    torrent_file=TorrentFileReader._create_multi_file_torrent_from_info(info),
                    announce_list=announce_list,
                    comment=comment,
                    created_by=created_by,
                    creation_date=creation_date,
                )
            else:
                print("single_file torrent")  # todo move to debug mode only

                return MetaInfoFile(
                    announce=announce,
                    info_hash=TorrentFileReader.create_info_hash(info),
                    torrent_file=TorrentFileReader.create_single_file_torrent_from_info(info),
                    announce_list=announce_list,
                    comment=comment,
                    created_by=created_by,
                    creation_date=creation_date,
                )


    @staticmethod
    def _create_multi_file_torrent_from_info(info) -> MultiFileTorrent:
        name = info[b'name']
        piece_length = info[b'piece length']
        pieces = info[b'pieces']

        torrent_files = []
        for file in info[b'files']:
            md5sum = None
            if b'md5sum' in file:
                md5sum = file[b'md5sum']
            torrent_files.append(
                FileFromMultiFileTorrent(
                    length=file[b'length'],
                    path=file[b'path'],
                    md5sum=md5sum
                )
            )

        return MultiFileTorrent(
            name=name,
            piece_length=piece_length,
            pieces=wrap(pieces, 20),
            files=torrent_files
        )

    @staticmethod
    def create_single_file_torrent_from_info(info) -> SingleFileTorrent:
        length = info[b'length']
        name = info[b'name']
        piece_length = info[b'piece length']
        pieces = info[b'pieces']
        md5sum = None
        if b'md5sum' in info:
            md5sum = info[b'md5sum']

        return SingleFileTorrent(
            name=name,
            piece_length=piece_length,
            pieces=wrap(pieces, 20),
            length=length,
            md5sum=md5sum
        )

    @staticmethod
    def create_info_hash(info) -> bytes:
        sha1 = hashlib.sha1()
        sha1.update(bencoder.encode(info)) 
        return sha1.digest()[:20] # docs state that it should be 20 bytes length, but sha1 may be longer just take first 20 or what? todo find out


print(str(TorrentFileReader.read_file("test_resources/test.jpg.torrent")))
