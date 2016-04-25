import logging
import socket
import struct

LOG = logging.getLogger(__name__)

HEADER = struct.Struct('!HI')
HEADER_LENGTH = HEADER.size


def parse_header(header):
    """Uses HEADER struct to unpack the header.

    :param header: the packed header
    :type header: bytes

    :return: tuple (msgtype, size)
    :rtype: tuple
    """
    return HEADER.unpack(header)


def create_packet(msgtype, payload):
    """Uses HEADER struct to prepare the heaader and create the packet

    :param msgtype: the message type
    :type msgtype: int

    :param payload: the encoded payload
    :type payload: bytes

    :return: the packet
    :rtype: bytes
    """
    header = HEADER.pack(msgtype, len(payload))
    return header + payload


class Connection:
    """Application layer handler.

    Handles the communication with the server as the application layer. Uses TCP
    connection to communicate with the server, and is configurable using the
    client config file.

    :param config: the network section of the config object
    :type config: instance of :class:`configparser.SectionProxy`
    """

    def __init__(self, config):
        ip, port = config['ServerIPAddress'], config.getint('ServerPort')
        LOG.info('Connecting to {}:{}'.format(ip, port))
        self.socket = socket.create_connection((ip, port))
        self.socket.setblocking(False)
        self.chunk_size = config.getint('ChunkSize')

        self.header = None
        self.payload = None

    def send(self, msgtype, payload):
        """Sends a packet via TCP to the server.

        :param msgtype: the message type
        :type msgtype: int

        :param payload: the encoded payload
        :type payload: bytes
        """
        self.socket.sendall(create_packet(msgtype, payload))

    def recv(self):
        """Receives a single packet via TCP from the server.

        :return: tuple (msgtype, encoded_payload) if available
        :rtype: tuple or None
        """
        def read(size):
            try:
                data = self.socket.recv(size)
                return data
            except BlockingIOError:
                pass

        if self.header is None:
            header = read(HEADER_LENGTH)
            if header is None:
                return
            self.header = parse_header(header)
            LOG.debug('Received header: type={} size={}'.format(self.header[0], self.header[1]))

        if self.header is not None:
            while True:
                self.payload = self.payload or bytearray()

                if len(self.payload) == self.header[1]:
                    break

                size = (
                    self.chunk_size
                    if self.chunk_size <= self.header[1] - len(self.payload)
                    else self.header[1] - len(self.payload)
                )
                data = read(size)
                if data:
                    self.payload.extend(data)
                    LOG.debug('Received payload: {} bytes'.format(size))

        if self.header is not None and self.payload is not None and len(self.payload) == self.header[1]:
            # Returns the tuple (msgtype, payload)
            msgtype, payload = self.header[0], self.payload
            self.header, self.payload = None, None
            LOG.debug('Received message {}'.format(msgtype))
            return msgtype, payload
