import struct
import unittest

from bitarray import bitarray

from model.pwp_message import PwpPiece, PwpMessage, PwpId, PwpRequest, PwpCancel, PwpHave, MessagesUtil


class TestPwpMessages(unittest.TestCase):

    def test_pwp_message_to_bytes(self):
        msg = PwpMessage(1, PwpId.HAVE, b'1234')
        should_be_equal_to = struct.pack('!I', 1) + bytes([4]) + b'1234'
        self.assertEqual(msg.to_bytes(), should_be_equal_to)

    def test_pwp_message_from_bytes(self):
        data = struct.pack('!I', 1) + bytes([4]) + b'1234'
        msg = PwpMessage(1, PwpId.HAVE, b'1234')
        self.assertEqual(PwpMessage.from_bytes(data), msg)

    def test_piece_to_bytes(self):
        piece = PwpPiece(1, 2222, b'1234')
        should_be_equal_to = struct.pack('!2I', 1, 2222) + b'1234'
        self.assertEqual(piece.to_bytes(), should_be_equal_to)

    def test_piece_from_bytes(self):
        piece = PwpPiece(1, 2222, b'1234')
        data = struct.pack('!2I', 1, 2222) + b'1234'
        self.assertEqual(PwpPiece.from_bytes(data), piece)

    def test_pwp_request_from_bytes(self):
        request = PwpRequest(1, 2222, 3)
        data = struct.pack('!3I', 1, 2222, 3)
        self.assertEqual(PwpRequest.from_bytes(data), request)

    def test_pwp_request_to_bytes(self):
        request = PwpRequest(1, 2222, 3)
        data = struct.pack('!3I', 1, 2222, 3)
        self.assertEqual(request.to_bytes(), data)

    def test_pwp_have_to_bytes(self):
        have = PwpHave(1)
        data = struct.pack('!I', 1)
        self.assertEqual(have.to_bytes(), data)

    def test_pwp_have_from_bytes(self):
        have = PwpHave(1)
        data = struct.pack('!I', 1)
        self.assertEqual(PwpHave.from_bytes(data), have)

    def test_pwp_cancel_to_bytes(self):
        cancel = PwpCancel(1, 2222, 3)
        data = struct.pack('!3I', 1, 2222, 3)
        self.assertEqual(cancel.to_bytes(), data)

    def test_pwp_cancel_from_bytes(self):
        cancel = PwpCancel(1, 2222, 3)
        data = struct.pack('!3I', 1, 2222, 3)
        self.assertEqual(PwpCancel.from_bytes(data), cancel)

    def test_pwp_cancel_length(self):
        cancel = PwpCancel(1, 2222, 3)
        self.assertEqual(12, cancel.get_length())

    def test_pwp_have_length(self):
        have = PwpHave(3123)
        self.assertEqual(4, have.get_length())

    def test_pwp_piece_length(self):
        piece = PwpPiece(1, 2, b'0123456789')
        self.assertEqual(piece.get_length(), 18)

    def test_pwp_request_length(self):
        req = PwpRequest(1, 2, 3)
        self.assertEqual(req.get_length(), 12)

    def test_id_length(self):
        self.assertEqual(PwpMessage.get_id_length(), 1)


class TestPwpMessagesCreation(unittest.TestCase):

    def test_from_request(self):
        request = PwpRequest(1, 2, 3)
        data = struct.pack('!3I', 1, 2, 3)
        msg = PwpMessage(13, PwpId.REQUEST, data)
        self.assertEqual(request.to_pwp_message(), msg)

    def test_from_piece(self):
        piece = PwpPiece(1, 2, b'1234')
        data = struct.pack('!2I', 1, 2) + b'1234'
        msg = PwpMessage(13, PwpId.PIECE, data)
        self.assertEqual(piece.to_pwp_message(), msg)

    def test_from_have(self):
        have = PwpHave(1)
        data = struct.pack('!I', 1)
        msg = PwpMessage(5, PwpId.HAVE, data)
        self.assertEqual(have.to_pwp_message(), msg)

    def test_from_cancel(self):
        cancel = PwpCancel(1, 2, 3)
        data = struct.pack('!3I', 1, 2, 3)
        msg = PwpMessage(13, PwpId.CANCEL, data)
        self.assertEqual(cancel.to_pwp_message(), msg)

    def test_bitfield_message(self):
        data = b'1234'
        arr = bitarray()
        arr.frombytes(data)
        msg = MessagesUtil.generate_bitfield_message(arr)
        self.assertEqual(msg, PwpMessage(5, PwpId.BITFIELD, b'1234'))


if __name__ == '__main__':
    unittest.main()
