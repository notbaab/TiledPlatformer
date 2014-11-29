import sys
import socket
import time

if sys.version_info > (3, 0):
  import pickle as pickle
else:
  import cPickle as pickle

import pygame

SOCKET_DEL = '*ET*'.encode('utf-8')
LEFT_SCORE_TILE = [1, 1]
RIGHT_SCORE_TILE = [3, 1]
INFO_TILE = [2, 1]


def get_whole_packet(open_sock, amount_of_data=81852):
  """
  Gets the entire packet by checking if the string delimiter is in the bytestream

  :param open_sock: the socket you are receiving the packet from
  :type open_sock: socket
  :param amount_of_data: the max amount of data to receive
  :type amount_of_data: int
  """
  data = ''.encode('utf-8')
  while True:
    data += open_sock.recv(amount_of_data)
    split = data.split(SOCKET_DEL)  # split at newline, as per our custom protocol
    if len(split) != 2:  # it should be 2 elements big if it got the whole message
      pass
    else:
      # got all the data, unserialize and return it
      data = pickle.loads(split[0])
      return data  # returns just the pickled string


class NetworkedTileGame(object):
  def __init__(self, tile):
    """
    The Client objects of the display wall. This is just an interface that needs
        be obeyed for the Server to use the game properly
    :param tile: The tile position of the display this node is attached to
    :type tile: tuple
    """
    self.tile = tile

  def init_game(self, initial_data):
    """
    The second constructor for the display node. The first function called after 
        the connection is made with the master node. Should be used to set the initial 
        game state and create all the paired client game objects.
    :param initial_data: The initial data that a display node will need. Typically all 
        the starting game objects and any other initialization code.
    :type initial_data: dict
    """
    raise NotImplementedError

  def update(self, data):
    """
    Called by the client every time it receives data. This is where you put 
        logic in to handle the data that is passed every frame. I suggest you 
        have a simple switch statement that reads a state variable from data and
        pass that to a different function. 
    
    :param data: The packet for that frame
    :type initial_data: dict
    """
    raise NotImplementedError

  def translate_to_local(self, data):
    """Translates the given data to the local node."""
    raise NotImplementedError

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    raise NotImplementedError


class NetworkedMasterGame(object):
  """Interface for the Master node game."""

  def __init__(self):
    """Initialize the game state."""
    super(NetworkedMasterGame, self).__init__()

  def init_game(self):
    """
    Build the initial data packet that will be sent to all the display nodes

    :returns: The initial data packet to send to all the nodes
    :rytpe: dict
    """
    raise NotImplementedError

  def update(self):
    """
    Called every frame by the server. Is the main game loop.

    :returns: the data packet to be sent to the display nodes
    :rtype: dict
    """
    raise NotImplementedError


class NetworkedObject(object):
  """
  Simple networked object that a game that has a list of attributes that 
      will be sent every time build_packet is called and can be read in with read_packet.
      There is a lot of room for improvment in this Class. It would be better if build
      packet checked if the attribute it was going to send has actually changed and 
      only send it if it has. As of now it's pretty dumb and just sends everything.
  """

  def __init__(self, attribute_list):
    """
    Accepts a list of attributes that will be looped over in build and 
        read in order to update the object. 

    :param attribute_list: list of variables in the subclass to be sent.
    :type attribute_list: list[str]"""
    self.attribute_list = attribute_list
    self.send_data = True

  def build_packet(self, accumulator):
    """
    Builds the data packet with the string of the attribute as the key to 
        the dictionary. 

    :param accumulator: An accumulator that has the current packet list to be sent
    :type accumulator: list[dictionary]
    """
    if self.send_data:
      packet = {}
      for attribute in self.attribute_list:
        packet[attribute] = self.__getattribute__(attribute)
      accumulator.append(packet)

  def read_packet(self, packet):
    """
    Reads packet and sets the value of the class to the value in the packet

    :param packet: the packet containing the new variable data
    :type packet: dict
    """
    for key, attibute in packet.items():
      self.__setattr__(key, attribute)
      # for attribute in self.attribute_list:
      # self.__setattr__(attribute, packet[attribute])


class Server(object):
  def __init__(self, game, ip_file=None, port=2000):
    """
    Initialize the server node to start a socket connection with every node
        specified in ip_file. If no ip file, then will make one connection with 
        local host

    :param ip_file: A text file with the list of ip addresses to connect to. 
    :type ip_file: str
    :param port: the port to connect to each ip address
    :type port: str or int
    :param game: An instance of a game 
    :type game: NetworkedMasterGame
    """
    self.game = game
    if not ip_file:
      ip_list = ['localhost']
      self.game.setup_local_host()
    else:
      ip_list = self._read_ip_file(ip_file)

    self.open_sockets(ip_list, port)

  def start_game(self):
    """Starts the game and sends the initial data packet to the nodes"""
    initial_packet = self.game.init_game()
    self.send(initial_packet)  # ack handled in the run function

  def run(self):
    """Main game loop. Continually calls update and sends the data to the display nodes."""
    recieved_packets = {}
    while True:
      send_struct = self.game.update(recieved_packets)
      if not send_struct:
        # nothing recieved indicates a kill order to the nodes
        self.kill()
      recieved_packets = self.recv()
      self.send(send_struct)

  def _read_ip_file(self, file):
    """read the ip file and make a list of ips to connect to"""
    ip_list = []
    ips = open(file, 'r')
    address = ips.readline().strip()
    ip_list = []
    while address:
      ip_list.append(address)
      address = ips.readline().strip()
    return ip_list

  def open_sockets(self, ip_list, port):
    """
    Make a list of socekts and opens a connection to all of them

    :param ip_list: a list of strings containing ip addresses to connect to
    :type ip_list: list
    :param port: the port to make the connection on
    :type port: int
    """
    self.socket_list = []
    for ip in ip_list:
      self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      self.socket_list[-1].connect((ip, port))

  def send(self, send_struct):
    """
    Sends data to all of the socket connections by serialization them and adding a 
        delimiter to the end of the packet to indicate the end of the stream

    :param send_struct: a python object that you want to send to all the cients
    :type send_struct: 
    """
    data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    for node in self.socket_list:
      node.sendall(data)

  def recv(self):
    """
    Receives data from all the display nodes

    :returns: a list of the packets received from the display nodes
    :rtype: list
    """
    return_list = []
    for node in self.socket_list:
      return_list.append(get_whole_packet(node))
    return return_list

  def kill(self):
    """sends the kill state to the nodes and exits"""
    data = pickle.dumps({'state': 'kill'}, pickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    for node in self.socket_list:
      node.sendall(data)
    time.sleep(2)
    sys.exit()


# TODO: Flesh out to add error handling
class Client(object):
  amount_of_data = 81852

  def __init__(self, ip_address, port, game):
    """
    Client class for the worker nodes. Handles synchronization with the master node.

    :param ip_address: the ip_address of the client to open the socket connection on
    :type ip_address: str
    :param port: which port to open the connection on
    :type port: int
    :param game: An instance of a the game to be played
    :type game: NetworkedTileGame
    """
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.bind((ip_address, port))
    self.game = game  # will handle giving data back to the game

  def open_connection(self):
    """Listen for one connection, accept it, and initialize the game"""
    self.socket.listen(1)
    self.open_sock, addr = self.socket.accept()
    init_data = get_whole_packet(self.open_sock)
    handshake = self.game.init_game(init_data)
    self.sync(handshake)
    print("connection made to " + str(addr))

  def close_connection(self, msg):
    """Close the socket connection"""
    print(msg)
    self.open_sock.shutdown(socket.SHUT_RDWR)
    self.open_sock.close()

  def recev_connection(self):
    """Receives the data packet, unserializes it, and sends an ack after done processing it"""
    # todo return something to know if time to quit
    data = get_whole_packet(self.open_sock)
    state_struct = self.process_request(data)
    self.sync(state_struct)

  def process_request(self, data):
    """
    Either kills the connection if a kill signal is sent or sends the data packet 
        to the games update function
    :param data: the data to be sent to the update function
    :type data: dict
    """
    if data['state'] == 'kill':
      pygame.quit()
      self.close_connection('Kill state')
      sys.exit()
    struct = self.game.update(data)
    return struct

  def sync(self, send_struct):
    """send response back to connecting to say processing is complete"""
    x = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    self.open_sock.sendall(x)


