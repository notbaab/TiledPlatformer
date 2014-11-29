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
    self.tile = tile

  def init_game(self, data):
    """over ride this method. """
    raise NotImplementedError

  def update(self, data):
    """Called by the client every time it receives data. This is where you put 
    logic in to handle the data. I suggest you have a simple switch 
    statement that reads a state variable from data and react that way."""
    raise NotImplementedError

  def clear(self, data):
    """override this method, only hook needed for the server"""
    raise NotImplementedError

  def translate_to_local(self, data):
    """translates the given data to the local node. Wrapper for call to game
    """
    raise NotImplementedError

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    raise NotImplementedError


class NetworkedMasterGame(object):
  """Interface for the Master node game."""

  def __init__(self):
    """Initialize the game state. Should build all the initial game objects"""
    super(NetworkedMasterGame, self).__init__()

  def get_initial_state(self):
    """Should loop over game state and return a data structure will be sent to 
    all nodes in the beginning of the game.
    :rtype: A python data structure to be sent to the tile nodes
    """
    raise NotImplementedError


class NetworkedObject(object):
  """simple networked object that a game that has a list of attributes that 
  will be sent every time build_packet is called and can be read in with read_packet.
  There is a lot of room for improvment in this Class. It would be better if build
  packet checked if the attribute it was going to send has actually changed and 
  only send it if it has. As of now it's pretty dumb and just sends everything.
  """

  def __init__(self, attribute_list):
    """Accepts a list of attributes that will be looped over in build and 
    read in order to update the object. 
    :param attribute_list: list of variables in the subclass to be sent.
    :type attribute_list: list[str]"""
    self.attribute_list = attribute_list
    self.send_data = True

  def build_packet(self, accumulator):
    """builds the data packet with the string of the attribute as the key to 
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
    """Reads packet and sets the value of the class to the value in the packet
    :param packet: the packet containing the new variable data
    :type packet: dict
    """
    for key, attibute in packet.items():
      self.__setattr__(key, attribute)
      # for attribute in self.attribute_list:
      # self.__setattr__(attribute, packet[attribute])


class Server(object):
  def __init__(self, game, ip_file=None, port=2000):
    """Initialize the server node to start a socket connection with every node
    specified in ip_list.
    :param ip_list: A text file with the list of ip addresses to connect to. 
    :type ip_list: str
    :param port: the port to connect to each ip address
    :type port: str or int
    :param game: The constructor for the game. Should be a 
    :type game: NetworkedGame
    """
    self.game = game
    if not ip_file:
      ip_list = ['localhost']
      self.game.setup_local_host()
    else:
      ip_list = self._read_ip_file(ip_file)

    self.open_sockets(ip_list, port)
    # self.state, initial_packet = self.game.init_game()
    # self.send(initial_packet)  

  def start_game(self):
    initial_packet = self.game.init_game()
    self.send(initial_packet)  # ack handled in the run function

  def run(self):
    recieved_packets = {}
    while True:
      send_struct = self.game.update(recieved_packets)
      if not send_struct:
        # nothing recieved indicates a kill order to the nodes
        self.kill()
      recieved_packets = self.recv()
      self.send(send_struct)

  def _read_ip_file(self, file):
    ip_list = []
    ips = open(file, 'r')
    address = ips.readline().strip()
    ip_list = []
    while address:
      ip_list.append(address)
      address = ips.readline().strip()
    return ip_list

  def open_sockets(self, ip_list, port):
    self.socket_list = []
    for ip in ip_list:
      self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      self.socket_list[-1].connect((ip, port))

  def send(self, send_struct):
    data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    for node in self.socket_list:
      node.sendall(data)

  def recv(self):
    return_list = []
    for node in self.socket_list:
      return_list.append(get_whole_packet(node))
    return return_list

  def kill(self):
    data = pickle.dumps({'state': 'kill'}, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    for node in self.socket_list:
      node.sendall(data)
    time.sleep(2)
    sys.exit()


# TODO: Flesh out to add error handling
class Client(object):
  """Client class for the worker nodes. Handles synchronization with the master
  node."""
  amount_of_data = 81852

  def __init__(self, ip_address, port, game):
    """"""
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.bind((ip_address, port))
    self.game = game  # will handle giving data back to the game

  def open_connection(self):
    self.socket.listen(1)
    self.open_sock, addr = self.socket.accept()
    init_data = get_whole_packet(self.open_sock)
    handshake = self.game.init_game(init_data)
    self.sync(handshake)
    print("connection made to " + str(addr))

  def close_connection(self, msg):
    # self.open_sock.sendall(msg)
    print(msg)
    self.open_sock.shutdown(socket.SHUT_RDWR)
    self.open_sock.close()

  def recev_connection(self):
    # todo return something to know if time to quit
    data = get_whole_packet(self.open_sock)
    state_struct = self.process_request(data)
    self.sync(state_struct)

  def process_request(self, data):
    if data['state'] == 'kill':
      pygame.quit()
      self.close_connection('Kill state')
      sys.exit()
    struct = self.game.update(data)
    return struct

  def sync(self, send_struct):
    # send response back to connecting to say processing is complete
    x = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    self.open_sock.sendall(x)


