import sys
import socket
import cPickle

SOCKET_DEL = '*ET*'.encode('utf-8')
LEFT_SCORE_TILE = [1, 1]
RIGHT_SCORE_TILE = [3, 1]
INFO_TILE = [2, 1]


class NetworkGame(object):
  def __init__(self, tile):
    self.tile = tile
    if tile[0] == LEFT_SCORE_TILE[0] and tile[1] == LEFT_SCORE_TILE[1]:
      self.score_tile = True
      self.player_score = 'p1'
    elif tile[0] == RIGHT_SCORE_TILE[0] and tile[1] == RIGHT_SCORE_TILE[1]:
      self.score_tile = True
      self.player_score = 'p2'
    else:
      self.score_tile = False
    if tile[0] == INFO_TILE[0] and tile[1] == INFO_TILE[1]:
      self.info_tile = True
    else:
      self.info_tile = False

  def init_game(self, data):
    """over ride this method. This will be the true constructor of the networked
    game, data will contain all the initial data for the game"""
    pass

  def update(self, data):
    """override this method, only hook needed for the server"""
    pass

  def clear(self, data):
    """override this method, only hook needed for the server"""
    pass

  def translate_to_local(self, data):
    """translates the given data to the local node. Wrapper for call to game
    """
    pass

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass


# TODO: Flesh out to add error handling
class Server():
  amount_of_data = 81852

  def __init__(self, ip_address, port, game):
    """Server class that handles dealing with requests"""
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.bind((ip_address, port))
    self.game = game  # will handle giving data back to the game

  # noinspection PyAttributeOutsideInit
  def open_connection(self):
    self.socket.listen(1)
    self.open_sock, addr = self.socket.accept()
    init_data = self.get_whole_packet()
    init_data = cPickle.loads(init_data)
    handshake = self.game.init_game(init_data)
    self.sync(handshake)
    print("connection made to " + str(addr))

  def close_connection(self, msg):
    self.open_sock.sendall(msg)
    self.open_sock.shutdown(socket.SHUT_RDWR)
    self.open_sock.close()

  def recev_connection(self):
    # todo return something to know if time to quit
    data = self.get_whole_packet()
    state_struct = self.process_request(data)
    self.sync(state_struct)

  def process_request(self, pickled_data):
    data = cPickle.loads(pickled_data)
    # print 'kill state' + str(data['kill_state'])
    if data['state'] == 'kill':
      self.close_connection('died')
      sys.exit()
    struct = self.game.update(data)
    return struct

  def get_whole_packet(self):
    data = ''.encode('utf-8')
    while True:
      data += self.open_sock.recv(self.amount_of_data)
      split = data.split(SOCKET_DEL)  # split at newline, as per our custom protocol
      if len(split) != 2:  # it should be 2 elements big if it got the whole message
        pass
      else:
        return split[0]  # returns just the pickled string

  def sync(self, send_struct):
    # send response back to connecting to say processing is complete
    x = cPickle.dumps(send_struct, cPickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    self.open_sock.sendall(x)
    # if send_struct['state'] == 'over':
    #   # clear screen and wait for handshake to proceed
    #   data = self.get_whole_packet()
    #   self.game.clear()
    #   # once it recieves the signal to go, erase previous graphics
    #   x = pickle.dumps('go', pickle.HIGHEST_PROTOCOL) + SOCKET_DEL
    #   self.open_sock.sendall(x)


