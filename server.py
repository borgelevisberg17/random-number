import socket
import threading
import json
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from database import save_multiplayer_score, fetch_online_sessions, clear_expired_sessions

class GameServer:
    def __init__(self, host='localhost', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(8)
        self.clients = {}
        self.games = {}
        self.lock = threading.Lock()
        self.cipher = Fernet(Fernet.generate_key())  # Chave de criptografia por sessão
        print(f"Servidor iniciado em {host}:{port}")

    def encrypt(self, message):
        return self.cipher.encrypt(json.dumps(message).encode('utf-8'))

    def decrypt(self, data):
        try:
            return json.loads(self.cipher.decrypt(data).decode('utf-8'))
        except:
            return None

    def broadcast(self, session_id, message):
        with self.lock:
            for client, info in list(self.clients.items()):
                if info['session_id'] == session_id:
                    try:
                        client.send(self.encrypt(message))
                    except:
                        client.close()
                        del self.clients[client]

    def validate_input(self, data):
        if not isinstance(data, dict):
            return False
        if len(json.dumps(data)) > 1024:  # Limite de tamanho da mensagem
            return False
        return True

    def handle_client(self, client, address):
        try:
            data = self.decrypt(client.recv(2048))
            if not self.validate_input(data):
                client.send(self.encrypt({"status": "error", "message": "Dados inválidos!"}))
                client.close()
                return
            
            session_id = data.get('session_id', 'default')
            player = data.get('player', '')
            mode = data.get('mode', '1x1')
            team = data.get('team', None)
            
            if len(player) > 20 or not player.isalnum():
                client.send(self.encrypt({"status": "error", "message": "Nome de jogador inválido!"}))
                client.close()
                return
            
            with self.lock:
                for _, info in self.clients.items():
                    if info['session_id'] == session_id and info['player'] == player:
                        client.send(self.encrypt({"status": "error", "message": "Jogador já conectado!"}))
                        client.close()
                        return
                
                self.clients[client] = {
                    'session_id': session_id,
                    'player': player,
                    'mode': mode,
                    'team': team,
                    'address': address,
                    'last_active': datetime.now(),
                    'confirmed': False
                }
                save_online_session(session_id, player, address[0], address[1])
            
            client.send(self.encrypt({"status": "connected", "player": player, "key": self.cipher._encryption_key.decode()}))
            
            while True:
                data = self.decrypt(client.recv(2048))
                if not data or not self.validate_input(data):
                    break
                
                self.clients[client]['last_active'] = datetime.now()
                action = data.get('action')
                
                if action == 'confirm':
                    self.handle_confirmation(client, session_id, data.get('confirmed', False))
                elif action == 'start_game':
                    self.start_game(client, session_id, mode, data.get('difficulty', 20), data.get('rounds', 1), data.get('tournament', False))
                elif action == 'guess':
                    self.handle_guess(client, session_id, data.get('number'), data.get('guess'))
                elif action == 'rematch':
                    self.handle_rematch(client, session_id, data.get('confirmed', False))
        
        except Exception as e:
            print(f"Erro no cliente {address}: {e}")
        finally:
            with self.lock:
                if client in self.clients:
                    del self.clients[client]
            client.close()

    def cleanup_inactive_clients(self):
        with self.lock:
            for client, info in list(self.clients.items()):
                if datetime.now() - info['last_active'] > timedelta(minutes=5):
                    client.close()
                    del self.clients[client]
            clear_expired_sessions()

    def start_game(self, client, session_id, mode, max_number, rounds, tournament):
        with self.lock:
            players = [info['player'] for c, info in self.clients.items() if info['session_id'] == session_id and info['confirmed']]
            teams = {}
            if mode == '2x2':
                for c, info in self.clients.items():
                    if info['session_id'] == session_id and info['team']:
                        if info['team'] not in teams:
                            teams[info['team']] = []
                        teams[info['team']].append(info['player'])
            
            min_players = 4 if mode == '2x2' else 2
            if len(players) < min_players:
                client.send(self.encrypt({"status": "error", "message": f"Mínimo de {min_players} jogadores necessários!"}))
                return
            if mode == '2x2' and any(len(team_players) != 2 for team_players in teams.values()):
                client.send(self.encrypt({"status": "error", "message": "Cada equipe deve ter exatamente 2 jogadores!"}))
                return
            
            if tournament and len(players) not in [2, 3, 4]:
                client.send(self.encrypt({"status": "error", "message": "Torneio requer 2, 3 ou 4 jogadores/equipes!"}))
                return
            
            if session_id not in self.games:
                self.games[session_id] = {
                    'mode': mode,
                    'max_number': max_number,
                    'rounds': rounds if not tournament or len(players) < 4 else 1,
                    'current_round': 0,
                    'scores': {player: 0 for player in players},
                    'numbers': {player: [] for player in players},
                    'attempts': {player: {} for player in players},
                    'teams': teams if mode == '2x2' else None,
                    'tournament': tournament,
                    'tournament_phase': 'semifinals' if tournament and len(players) == 4 else 'rounds',
                    'tournament_matches': [] if tournament else None
                }
                if tournament and len(players) == 4:
                    self.games[session_id]['tournament_matches'] = [
                        (players[0], players[1]),
                        (players[2], players[3])
                    ]
            
            self.start_round(session_id)

    def start_round(self, session_id):
        game = self.games[session_id]
        game['current_round'] += 1
        
        if game['tournament'] and game['tournament_phase'] == 'semifinals':
            self.start_tournament_round(session_id)
            return
        elif game['tournament'] and game['tournament_phase'] == 'final':
            self.start_tournament_final(session_id)
            return
        elif game['current_round'] > game['rounds']:
            self.end_game(session_id)
            return
        
        for player in game['scores']:
            game['numbers'][player] = [random.randint(1, game['max_number']) for _ in range(5)]
            game['attempts'][player] = {i: {'attempts': 0, 'hint_used': False} for i in range(1, 6)}
        
        self.broadcast(session_id, {
            "status": "start_round",
            "round": game['current_round'],
            "message": f"Rodada {game['current_round']}/{game['rounds']}"
        })

    def start_tournament_round(self, session_id):
        game = self.games[session_id]
        for match in game['tournament_matches']:
            for player in match:
                game['numbers'][player] = [random.randint(1, game['max_number']) for _ in range(5)]
                game['attempts'][player] = {i: {'attempts': 0, 'hint_used': False} for i in range(1, 6)}
        
        self.broadcast(session_id, {
            "status": "start_tournament_round",
            "phase": game['tournament_phase'],
            "matches": game['tournament_matches'],
            "message": f"Iniciando {game['tournament_phase']}"
        })

    def start_tournament_final(self, session_id):
        game = self.games[session_id]
        for player in game['tournament_matches'][0]:
            game['numbers'][player] = [random.randint(1, game['max_number']) for _ in range(5)]
            game['attempts'][player] = {i: {'attempts': 0, 'hint_used': False} for i in range(1, 6)}
        
        self.broadcast(session_id, {
            "status": "start_tournament_round",
            "phase": game['tournament_phase'],
            "matches": game['tournament_matches'],
            "message": "Iniciando final"
        })

    def handle_guess(self, client, session_id, number_idx, guess):
        game = self.games[session_id]
        player = self.clients[client]['player']
        
        try:
            number_idx = int(number_idx)
            if number_idx not in range(1, 6):
                client.send(self.encrypt({"status": "error", "message": "Índice de número inválido!"}))
                return
        except ValueError:
            client.send(self.encrypt({"status": "error", "message": "Índice de número inválido!"}))
            return
        
        secret_number = game['numbers'][player][number_idx - 1]
        attempts = game['attempts'][player][number_idx]['attempts']
        hint_used = game['attempts'][player][number_idx]['hint_used']
        
        if guess == 'dica' and not hint_used:
            game['attempts'][player][number_idx]['hint_used'] = True
            client.send(self.encrypt({
                "status": "hint",
                "message": f"Dica: O número é {'par' if secret_number % 2 == 0 else 'ímpar'}!"
            }))
            return
        
        try:
            guess = int(guess)
        except ValueError:
            client.send(self.encrypt({"status": "error", "message": "Insira um número inteiro ou 'dica'!"}))
            return
        
        game['attempts'][player][number_idx]['attempts'] += 1
        if guess < secret_number:
            client.send(self.encrypt({"status": "guess", "message": "Muito baixo!"}))
        elif guess > secret_number:
            client.send(self.encrypt({"status": "guess", "message": "Muito alto!"}))
        else:
            points = max(1, 4 - game['attempts'][player][number_idx]['attempts'] - (1 if hint_used else 0))
            game['scores'][player] += points
            client.send(self.encrypt({
                "status": "correct",
                "message": f"Acertou o número {number_idx}! (+{points} pontos)"
            }))
            game['attempts'][player][number_idx]['attempts'] = 4  # Marca como concluído
        
        if all(game['attempts'][player][i]['attempts'] >= 3 or game['numbers'][player][i - 1] == guess for i in range(1, 6)):
            self.broadcast(session_id, {
                "status": "player_finished",
                "player": player,
                "score": game['scores'][player]
            })
            if game['tournament']:
                self.check_tournament_progress(session_id)
            elif all(all(game['attempts'][p][i]['attempts'] >= 3 for i in range(1, 6)) for p in game['scores']):
                self.end_round(session_id)

    def check_tournament_progress(self, session_id):
        game = self.games[session_id]
        if game['tournament_phase'] == 'semifinals':
            finished = all(all(game['attempts'][p][i]['attempts'] >= 3 for i in range(1, 6)) for match in game['tournament_matches'] for p in match)
            if finished:
                winners = []
                for match in game['tournament_matches']:
                    score1, score2 = game['scores'][match[0]], game['scores'][match[1]]
                    winner = match[0] if score1 > score2 else match[1]
                    winners.append(winner)
                    save_multiplayer_score(match[0], game['teams'][match[0]][0] if game['mode'] == '2x2' else None, 1 if score1 > score2 else 0, score1, is_tournament=1)
                    save_multiplayer_score(match[1], game['teams'][match[1]][0] if game['mode'] == '2x2' else None, 1 if score2 > score1 else 0, score2, is_tournament=1)
                
                game['tournament_matches'] = [(winners[0], winners[1])]
                game['tournament_phase'] = 'final'
                self.start_tournament_final(session_id)
        elif game['tournament_phase'] == 'final':
            finished = all(all(game['attempts'][p][i]['attempts'] >= 3 for i in range(1, 6)) for p in game['tournament_matches'][0])
            if finished:
                self.end_game(session_id)

    def end_round(self, session_id):
        game = self.games[session_id]
        if game['mode'] == '1x1':
            max_score = max(game['scores'].values())
            winners = [p for p, s in game['scores'].items() if s == max_score]
            for player in game['scores']:
                wins = 1 if player in winners and len(winners) == 1 else 0
                save_multiplayer_score(player, None, wins, game['scores'][player], is_tournament=1 if game['tournament'] else 0)
        else:  # 2x2
            team_scores = {team: sum(game['scores'][p] for p in players) for team, players in game['teams'].items()}
            max_score = max(team_scores.values())
            winners = [t for t, s in team_scores.items() if s == max_score]
            for team, players in game['teams'].items():
                for player in players:
                    wins = 1 if team in winners and len(winners) == 1 else 0
                    save_multiplayer_score(player, team, wins, game['scores'][player], is_tournament=1 if game['tournament'] else 0)
        
        self.broadcast(session_id, {
            "status": "end_round",
            "round": game['current_round'],
            "scores": game['scores'],
            "teams": {team: sum(game['scores'][p] for p in players) for team, players in game['teams'].items()} if game['teams'] else None
        })
        self.start_round(session_id)

    def end_game(self, session_id):
        game = self.games[session_id]
        if game['mode'] == '1x1':
            max_score = max(game['scores'].values())
            winners = [p for p, s in game['scores'].items() if s == max_score]
            self.broadcast(session_id, {
                "status": "end_game",
                "message": f"{'Empate!' if len(winners) > 1 else f'{winners[0]} vence!'}",
                "scores": game['scores']
            })
        else:
            team_scores = {team: sum(game['scores'][p] for p in players) for team, players in game['teams'].items()}
            max_score = max(team_scores.values())
            winners = [t for t, s in team_scores.items() if s == max_score]
            self.broadcast(session_id, {
                "status": "end_game",
                "message": f"{'Empate!' if len(winners) > 1 else f'{winners[0]} vence!'}",
                "scores": game['scores'],
                "teams": team_scores
            })
        
        self.broadcast(session_id, {"status": "rematch_prompt", "message": "Deseja revanche? (s/n)"})

    def handle_rematch(self, client, session_id, confirmed):
        if confirmed:
            self.clients[client]['confirmed'] = True
            if all(info['confirmed'] for info in self.clients.values() if info['session_id'] == session_id):
                game = self.games[session_id]
                self.games[session_id] = {
                    'mode': game['mode'],
                    'max_number': game['max_number'],
                    'rounds': game['rounds'],
                    'current_round': 0,
                    'scores': {p: 0 for p in game['scores']},
                    'numbers': {p: [] for p in game['scores']},
                    'attempts': {p: {} for p in game['scores']},
                    'teams': game['teams'],
                    'tournament': game['tournament'],
                    'tournament_phase': 'semifinals' if game['tournament'] and len(game['scores']) == 4 else 'rounds',
                    'tournament_matches': game['tournament_matches'] if game['tournament'] and len(game['scores']) == 4 else []
                }
                self.start_round(session_id)
        else:
            with self.lock:
                del self.clients[client]
            client.close()

    def handle_confirmation(self, client, session_id, confirmed):
        if confirmed:
            self.clients[client]['confirmed'] = True
            self.broadcast(session_id, {
                "status": "confirmation",
                "player": self.clients[client]['player'],
                "message": f"{self.clients[client]['player']} confirmou participação!"
            })
            if all(info['confirmed'] for info in self.clients.values() if info['session_id'] == session_id):
                self.start_game(client, session_id, self.clients[client]['mode'], self.games.get(session_id, {}).get('max_number', 20), self.games.get(session_id, {}).get('rounds', 1), self.games.get(session_id, {}).get('tournament', False))
        else:
            with self.lock:
                del self.clients[client]
            client.close()

    def run(self):
        threading.Thread(target=self.cleanup_inactive_clients, daemon=True).start()
        while True:
            client, address = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client, address)).start()