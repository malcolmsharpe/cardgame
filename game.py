MAX_PLAYERS = 2


class Error(Exception):
  pass


class TooManyPlayersError(Error):
  pass


class Game(object):
  def __init__(self, game_id):
    self.creator = None
    self.game_id = game_id
    self.players = []
    self.is_started = False

    self.move_request = None

    self.current_player_index = 0
    self.moves = 0
    self.winner_index = None

  # Pre-game setup
  def AddPlayer(self, player):
    if self.IsFull():
      raise TooManyPlayersError()

    if self.creator is None:
      self.creator = player

    self.players.append(player)

  def IsFull(self):
    return len(self.players) >= MAX_PLAYERS

  def IsStarted(self):
    return self.is_started

  # Running the game
  def Start(self):
    assert self.IsFull()
    assert self.move_request is None

    self.move_request = PassOrWinMoveRequest()
    self.is_started = True

  def Play(self, move):
    self.move_request = self.move_request.UpdateGame(self, move)

  # State queries
  def GetCurrentPlayer(self):
    return self.players[self.current_player_index]


class PassOrWinMoveRequest(object):
  def __init__(self):
    pass

  def UpdateGame(self, game, win):
    if win:
      game.winner_index = game.current_player_index
      return None
    else:
      game.current_player_index = (game.current_player_index + 1) % 2
      game.moves += 1
      return PassOrWinMoveRequest()
