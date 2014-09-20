import pygame
import sys
#import ipdb
from pygame.locals import *
import world as wd
import engine as eng
import socket
import pickle

# TODO: Maybe it's time to move away from the socket del? That will also require moving off pickling
SOCKET_DEL = '*ET*'.encode('utf-8')
loc = []
FPS = pygame.time.Clock()
TICK = 60
GRID_SPACE = [0, 0]
# DISPLAY_SIZE = [600, 600]
DISPLAY_SIZE = {"x": 600, "y": 600}
BEZZEL_SIZE = [30, 30]


# TODO: have a platformer game class that has all the similar components of the render and 
# master node, and inherit from that?
class MasterPlatformer(object):
    """Class for the platformer head node"""

    def __init__(self, localhosts=1):
        super(MasterPlatformer, self).__init__()
        pygame.init()

        self.game_objects = {}
        self.window = pygame.display.set_mode((60, 60))
        self.engine = eng.Engine()

        # TODO: Somehow figure out how to read all the map files that each node will have and build a map
        # off of those
        # load map
        self.game_objects['terrain'] = []
        self.game_objects['players'] = []
        self.game_objects['data_object'] = []

        for x in range(0, GRID_SPACE[0] + 1):
            for y in range(0, GRID_SPACE[1] + 1):
                map_json = self.engine.parse_json("map" + str(x) + str(y) + ".json")
                for tile in map_json['floors']:
                    self.game_objects['terrain'].append(
                        wd.SimpleScenery(int(tile["x"]) + x * DISPLAY_SIZE["x"], int(tile["y"]) + y * DISPLAY_SIZE["y"],
                                         int(tile["width"]), int(tile["height"]), (255, 255, 000)))
                for player in map_json['players']:
                    self.game_objects['players'].append(wd.Player(int(player["x"]) + x * DISPLAY_SIZE["x"],
                                                                  int(player["y"]) + y * DISPLAY_SIZE["y"], 30, 30,
                                                                  sprite_sheet='Player.png'))
                for data in map_json['data_object']:
                    self.game_objects['data_object'].append(wd.Data(int(data["x"]) + x * DISPLAY_SIZE["x"],
                                                                    int(data["y"]) + y * DISPLAY_SIZE["y"],
                                                                    int(data["width"]),
                                                                    int(data["height"]),
                                                                    color=(255, 255, 0)))
        send_struct = {}
        # build the initial data packet
        for obj_type, obj_list in self.game_objects.items():
            send_struct[obj_type] = []
            # print(obj_list)
            for game_obj in obj_list:
                send_dict = {"rect": [game_obj.rect.x, game_obj.rect.y, game_obj.rect.width,
                                      game_obj.rect.height], "id": game_obj.id, "color": game_obj.color,
                             "constructor": type(game_obj).__name__}
                send_struct[obj_type].append(send_dict)

        print(send_struct)

        data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
        # TODO: Stop being lazy and read from file.
        # ip_list
        self.ip_list = []
        for x in range(0, localhosts):
            self.ip_list.append(('localhost', 2000 + x))

        self.socket_list = []
        for node in self.ip_list:
            self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            print(node)
            self.socket_list[-1].connect(node)
            self.socket_list[-1].sendall(data)

        for node in self.socket_list:
            self.get_whole_packet(node)

        # TODO: Send initial player objects to the nodes. That will require a kind
        # Setup state to be added.
        self.state = 'play'
        print(self.game_objects)

    def run(self):
        while True:
            if self.state == 'play':
                data, self.state = self.play_frame()
            else:
                ipdb.set_trace()

            FPS.tick(TICK)

    def play_frame(self):
        # TODO: Add ability to change controls
        player1 = self.game_objects['players'][0];
        player2 = self.game_objects['players'][1];
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    player1.move_left()
                if event.key == K_RIGHT:
                    player1.move_right()
                if event.key == K_UP:
                    player1.jump()
                if event.key == K_a:
                    player2.move_left()
                if event.key == K_d:
                    player2.move_right()
                if event.key == K_w:
                    player2.jump()
            if event.type == KEYUP:
                  if event.key == K_LEFT:
                      player1.stop_left()
                  if event.key == K_RIGHT:
                      player1.stop_right()
                  if event.key == K_a:
                      player2.stop_left()
                  if event.key == K_d:
                      player2.stop_right()
        self.engine.physics_simulation(self.game_objects['players'] + self.game_objects['data_object'],
                                       self.game_objects['terrain'])

        # TODO: Build network packet in a little better
        # build network packet
        # send_struct = {'state': 'play',
        # 'player_loc': [self.game_objects['players'][0].rect.x, self.game_objects['players'][0].rect.y]}

        # send_struct['data_object'] = []
        # for data_object in self.game_objects['data_object']:
        # send_struct['data_object'].append((data_object.rect.x, data_object.rect.y))

        # This should be the final packet structure.
        send_struct = {'state': 'play'}
        game_objects = []
        self.engine.loop_over_game_dict_att(self.game_objects, 'build_packet', game_objects)
        # print(game_objects)
        send_struct['game_objects'] = game_objects

        data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
        for node in self.socket_list:
            node.sendall(data)

        return_list = []
        for node in self.socket_list:
            return_list.append(self.get_whole_packet(node))
        # TODO: return real data
        return '', 'play'

    def get_whole_packet(self, sock):
        """ensures that we receive the whole stream of data"""
        data = ''.encode('utf-8')
        while True:
            data += sock.recv(4024)
            split = data.split(SOCKET_DEL)  # split at newline, as per our custom protocol
            if len(split) != 2:  # it should be 2 elements big if it got the whole message
                pass
            else:
                x = pickle.loads(split[0])
                return x

if __name__ == '__main__':
    game = MasterPlatformer(localhosts=1)
    game.run()
