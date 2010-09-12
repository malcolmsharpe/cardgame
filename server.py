#!/usr/bin/env python2.6
from game import Game, PassOrWinMoveRequest
import itertools
import json
import os
import tornado.web
import tornado.websocket
import tornado.httpserver

PORT = 8888

settings = {
  'template_path' : os.path.join(os.path.dirname(__file__), 'templates'),
  'static_path' : os.path.join(os.path.dirname(__file__), 'static'),
}


# Exceptions
class Error(object):
  pass


class UnknownMessageTypeError(Error):
  pass


class WrongTurnError(Error):
  pass


# Authentication
class ChooseNameHandler(tornado.web.RequestHandler):
  def get(self):
    self.render('choosename.html')

  def post(self):
    name = self.get_argument('name').strip()
    self.set_cookie('name', name)
    self.redirect('/')


class LoginMixin(object):
  def get_current_user(self):
    return self.get_cookie('name')

  def get_login_url(self):
    return '/choosename'


# Game management handlers
games = {}


class IndexHandler(LoginMixin, tornado.web.RequestHandler):
  @tornado.web.authenticated
  def get(self):
    self.render('index.html', games=games.values())


class CreateGameHandler(LoginMixin, tornado.web.RequestHandler):
  _game_ids = itertools.count()

  @tornado.web.authenticated
  def post(self):
    game_id = self._game_ids.next()
    game = Game(game_id)
    game.AddPlayer(self.current_user)
    games[game_id] = game

    self.redirect('/play/%d' % game_id)


class JoinGameHandler(LoginMixin, tornado.web.RequestHandler):
  @tornado.web.authenticated
  def post(self):
    game_id = int(self.get_argument('gameid'))
    game = games[game_id]
    game.AddPlayer(self.current_user)

    self.redirect('/play/%d' % game_id)


class PlayHandler(LoginMixin, tornado.web.RequestHandler):
  @tornado.web.authenticated
  def get(self, game_id):
    self.render('play.html', game_id=game_id, user=self.current_user)


# Socket handler
sockets = []


def UpdateGameSockets(game):
  for socket in sockets:
    if socket.game.game_id == game.game_id:
      socket.SendUpdate()


class PlayWebSocketHandler(LoginMixin, tornado.websocket.WebSocketHandler):
  # WebSocketHandler methods
  def open(self, game_id):
    game_id = int(game_id)
    self.game = games[game_id]
    sockets.append(self)
    print '%d sockets' % len(sockets)

    if not self.game.IsStarted() and self.game.IsFull():
      self.game.Start()
      UpdateGameSockets(self.game)

  def on_message(self, message_json):
    if self.current_user != self.game.GetCurrentPlayer():
      raise WrongTurnError()

    message = json.loads(message_json)
    if message['type'] == 'win':
      self.game.Play(True)
    elif message['type'] == 'pass':
      self.game.Play(False)
    else:
      raise UnknownMessageTypeError()

    UpdateGameSockets(self.game)

  def on_close(self):
    sockets.remove(self)
    print '%d sockets' % len(sockets)

  # Other methods
  def SendUpdate(self):
    MOVE_REQUEST_DISPATCH = {
      PassOrWinMoveRequest: self.SendPassOrWinMoveRequest,
    }

    if (self.game.move_request is not None and
        self.game.GetCurrentPlayer() == self.current_user):
      fun = MOVE_REQUEST_DISPATCH[type(self.game.move_request)]
      fun()
    else:
      self.SendStateUpdate()

  def SendStateUpdate(self):
    self.write_message(json.dumps({
      'type': 'update',
      'html': self.render_string('playdiv/state.html', game=self.game),
    }))

  def SendPassOrWinMoveRequest(self):
    self.write_message(json.dumps({
      'type': 'update',
      'html': self.render_string('playdiv/pass_or_win.html', game=self.game),
    }))


application = tornado.web.Application([
  (r'/', IndexHandler),
  (r'/play/([0-9]+)', PlayHandler),
  (r'/choosename', ChooseNameHandler),
  (r'/creategame', CreateGameHandler),
  (r'/joingame', JoinGameHandler),
  (r'/websocket/([0-9]+)', PlayWebSocketHandler),
], **settings)


if __name__ == '__main__':
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(PORT)
  tornado.ioloop.IOLoop.instance().start()
