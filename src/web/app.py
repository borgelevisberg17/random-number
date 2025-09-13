import random
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from src.database import (
    save_score,
    fetch_scores,
    save_multiplayer_score,
    fetch_multiplayer_scores,
    save_wifi_player,
    remove_wifi_player,
    fetch_wifi_players,
    fetch_match_history,
    save_online_session,
    init_db
)
from src.game import (
    get_badge,
    validate_unique_name,
    get_rounds,
    get_difficulty,
    play_singleplayer,
    play_round,
)

init_db()

app = Flask(__name__)
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app)

# In-memory storage for game states
game_states = {}

def display_ranking(filter_type=None, player=None):
    scores = fetch_scores(filter_type, player)
    return scores

def display_multiplayer_ranking(mode="1x1", tournament_only=False):
    scores = fetch_multiplayer_scores(mode, tournament_only)
    return [(player, wins, f"{avg_score:.2f}", last_date, get_badge(wins)) for player, wins, avg_score, last_date in scores] if mode == "1x1" else [(team, player, wins, f"{avg_score:.2f}", last_date, get_badge(wins)) for team, player, wins, avg_score, last_date in scores]

def display_match_history():
    history = fetch_match_history()
    return [(player, team or "-", wins, score, date, "Torneio" if is_tournament else "Multiplayer") for player, team, wins, score, date, is_tournament in history]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/singleplayer', methods=['GET', 'POST'])
def singleplayer():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        difficulty = data.get('difficulty')
        guess = data.get('guess')
        game_state = data.get('game_state', {})

        if not name:
            valid, message = validate_unique_name(data.get('player_name'), [])
            if not valid:
                return jsonify({"status": "error", "message": message})
            name = data.get('player_name')
            max_number = get_difficulty(difficulty)
            game_state = play_singleplayer(name, max_number)
            return jsonify({"status": "start", "message": f"Adivinhe o número entre 1 e {max_number}, {name}! Você tem 6 tentativas.", "game_state": game_state})

        game_state['attempts'] += 1
        if game_state['attempts'] > 6:
            return jsonify({"status": "game_over", "message": f"Não foi dessa vez, {name}. O número era {game_state['secret_number']}."})

        if guess.lower() == 'dica' and not game_state['hint_used']:
            game_state['hint_used'] = True
            return jsonify({"status": "hint", "message": f"Dica: O número é {'par' if game_state['secret_number'] % 2 == 0 else 'ímpar'}!"})

        try:
            guess = int(guess)
        except ValueError:
            return jsonify({"status": "error", "message": "Insira um número inteiro ou 'dica'!"})

        if guess < game_state['secret_number']:
            return jsonify({"status": "guess", "message": "Muito baixo!"})
        elif guess > game_state['secret_number']:
            return jsonify({"status": "guess", "message": "Muito alto!"})
        else:
            final_attempts = game_state['attempts'] - (1 if game_state['hint_used'] else 0)
            if game_state['save_results'] and final_attempts > 0:
                save_score(name, final_attempts)
            return jsonify({"status": "game_over", "message": f"Parabéns, {name}! Você acertou em {final_attempts} tentativas!"})

    return render_template('singleplayer.html')

@app.route('/multiplayer', methods=['GET', 'POST'])
def multiplayer():
    if request.method == 'POST':
        data = request.json
        mode = data.get('mode')
        difficulty = data.get('difficulty')
        rounds = data.get('rounds')
        session_id = data.get('session_id', str(random.randint(1000, 9999)))
        player_name = data.get('player_name')
        players = data.get('players', {})
        team1_name = data.get('team1_name')
        team2_name = data.get('team2_name')

        valid, rounds_val = get_rounds(rounds)
        if not valid:
            return jsonify({"status": "error", "message": rounds_val})

        valid, message = validate_unique_name(player_name, list(players.values()) if players else [])
        if not valid:
            return jsonify({"status": "error", "message": message})

        max_number = get_difficulty(difficulty)
        game_state = game_states.get(session_id)
        if not game_state:
            game_state = {
                "session_id": session_id,
                "mode": mode,
                "max_number": max_number,
                "rounds": rounds_val,
                "current_round": 1,
                "players": {},
                "scores": {},
                "numbers": {},
                "attempts": {},
                "hint_used": {},
                "current_player": None,
                "game_over": False,
                "tournament_phase": "rounds"
            }

            if mode == "1x1":
                for player in [players.get('player1'), players.get('player2')]:
                    if player:
                        valid, message = validate_unique_name(player, list(players.values()))
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        game_state["players"][player] = {"sid": None}
                        game_state["scores"][player] = 0
                        game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                        game_state["attempts"][player] = []
                        game_state["hint_used"][player] = False
            else:  # 2x2
                for team, p1, p2 in [(team1_name, players.get('team1_p1'), players.get('team1_p2')), (team2_name, players.get('team2_p1'), players.get('team2_p2'))]:
                    if team:
                        valid, message = validate_unique_name(team, [team1_name, team2_name], is_team=True)
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        for player in [p1, p2]:
                            if player:
                                valid, message = validate_unique_name(player, list(players.values()))
                                if not valid:
                                    return jsonify({"status": "error", "message": message})
                                game_state["players"][player] = {"sid": None, "team": team}
                                game_state["scores"][player] = 0
                                game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                                game_state["attempts"][player] = []
                                game_state["hint_used"][player] = False
                        game_state["scores"][team] = 0

            game_states[session_id] = game_state

        return jsonify({"status": "start", "message": f"Sessão {session_id} criada ou acessada! Aguardando jogadores...", "session_id": session_id, "game_state": game_state})

    return render_template('multiplayer.html', mode=request.args.get('mode', '1x1'))

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    if request.method == 'POST':
        data = request.json
        mode = data.get('mode')
        difficulty = data.get('difficulty')
        rounds = data.get('rounds')
        session_id = data.get('session_id', str(random.randint(1000, 9999)))
        player_name = data.get('player_name')
        players = data.get('players', {})
        team1_name = data.get('team1_name')
        team2_name = data.get('team2_name')

        valid, rounds_val = get_rounds(rounds)
        if not valid:
            return jsonify({"status": "error", "message": rounds_val})

        valid, message = validate_unique_name(player_name, list(players.values()) if players else [])
        if not valid:
            return jsonify({"status": "error", "message": message})

        max_number = get_difficulty(difficulty)
        game_state = game_states.get(session_id)
        if not game_state:
            game_state = {
                "session_id": session_id,
                "mode": mode,
                "max_number": max_number,
                "rounds": 1 if mode == "1x1" and len(players) == 4 else rounds_val,
                "current_round": 1,
                "players": {},
                "scores": {},
                "numbers": {},
                "attempts": {},
                "hint_used": {},
                "current_player": None,
                "game_over": False,
                "tournament_phase": "semifinals" if mode == "1x1" and len(players) == 4 else "rounds"
            }

            if mode == "1x1":
                for player in [players.get('player1'), players.get('player2'), players.get('player3'), players.get('player4')]:
                    if player:
                        valid, message = validate_unique_name(player, list(players.values()))
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        game_state["players"][player] = {"sid": None}
                        game_state["scores"][player] = 0
                        game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                        game_state["attempts"][player] = []
                        game_state["hint_used"][player] = False
            else:  # 2x2
                for team, p1, p2 in [(team1_name, players.get('team1_p1'), players.get('team1_p2')), (team2_name, players.get('team2_p1'), players.get('team2_p2'))]:
                    if team:
                        valid, message = validate_unique_name(team, [team1_name, team2_name], is_team=True)
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        for player in [p1, p2]:
                            if player:
                                valid, message = validate_unique_name(player, list(players.values()))
                                if not valid:
                                    return jsonify({"status": "error", "message": message})
                                game_state["players"][player] = {"sid": None, "team": team}
                                game_state["scores"][player] = 0
                                game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                                game_state["attempts"][player] = []
                                game_state["hint_used"][player] = False
                        game_state["scores"][team] = 0

            game_states[session_id] = game_state

        return jsonify({"status": "start", "message": f"Sessão {session_id} criada ou acessada! Aguardando jogadores...", "session_id": session_id, "game_state": game_state})

    return render_template('tournament.html', mode=request.args.get('mode', '1x1'))

@app.route('/training', methods=['GET', 'POST'])
def training():
    if request.method == 'POST':
        data = request.json
        mode = data.get('mode')
        difficulty = data.get('difficulty')
        rounds = data.get('rounds')
        session_id = data.get('session_id', str(random.randint(1000, 9999)))
        player_name = data.get('player_name')
        players = data.get('players', {})
        team1_name = data.get('team1_name')
        team2_name = data.get('team2_name')

        valid, rounds_val = get_rounds(rounds)
        if not valid:
            return jsonify({"status": "error", "message": rounds_val})

        valid, message = validate_unique_name(player_name, list(players.values()) if players else [])
        if not valid:
            return jsonify({"status": "error", "message": message})

        max_number = get_difficulty(difficulty)
        game_state = game_states.get(session_id)
        if not game_state:
            game_state = {
                "session_id": session_id,
                "mode": mode,
                "max_number": max_number,
                "rounds": rounds_val,
                "current_round": 1,
                "players": {},
                "scores": {},
                "numbers": {},
                "attempts": {},
                "hint_used": {},
                "current_player": None,
                "game_over": False,
                "training": True
            }

            if mode == "singleplayer":
                game_state["players"][player_name] = {"sid": None}
                game_state["scores"][player_name] = 0
                game_state["numbers"][player_name] = [random.randint(1, max_number) for _ in range(5)]
                game_state["attempts"][player_name] = []
                game_state["hint_used"][player_name] = False
            elif mode == "1x1":
                for player in [player_name, players.get('player2')]:
                    if player:
                        valid, message = validate_unique_name(player, list(players.values()))
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        game_state["players"][player] = {"sid": None}
                        game_state["scores"][player] = 0
                        game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                        game_state["attempts"][player] = []
                        game_state["hint_used"][player] = False
            else:  # 2x2
                for team, p1, p2 in [(team1_name, player_name, players.get('team1_p2')), (team2_name, players.get('team2_p1'), players.get('team2_p2'))]:
                    if team:
                        valid, message = validate_unique_name(team, [team1_name, team2_name], is_team=True)
                        if not valid:
                            return jsonify({"status": "error", "message": message})
                        for player in [p1, p2]:
                            if player:
                                valid, message = validate_unique_name(player, list(players.values()))
                                if not valid:
                                    return jsonify({"status": "error", "message": message})
                                game_state["players"][player] = {"sid": None, "team": team}
                                game_state["scores"][player] = 0
                                game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
                                game_state["attempts"][player] = []
                                game_state["hint_used"][player] = False
                        game_state["scores"][team] = 0

            game_states[session_id] = game_state

        return jsonify({"status": "start", "message": f"Sessão de treino {session_id} criada ou acessada! Iniciando treino...", "session_id": session_id, "game_state": game_state})

    return render_template('training.html', mode=request.args.get('mode', 'singleplayer'))

@app.route('/wifi', methods=['GET', 'POST'])
def wifi():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        if action == 'list':
            return jsonify({"players": fetch_wifi_players()})
        elif action == 'add':
            name = data.get('name')
            valid, message = validate_unique_name(name, [], is_wifi=True)
            if not valid:
                return jsonify({"status": "error", "message": message})
            save_wifi_player(name)
            return jsonify({"status": "success", "message": f"Jogador {name} adicionado à rede Wi-Fi!"})
        elif action == 'remove':
            name = data.get('name')
            if name in fetch_wifi_players():
                remove_wifi_player(name)
                return jsonify({"status": "success", "message": f"Jogador {name} removido da rede Wi-Fi!"})
            return jsonify({"status": "error", "message": "Jogador não encontrado na rede Wi-Fi!"})
    return render_template('wifi.html')

@app.route('/ranking', methods=['GET', 'POST'])
def ranking():
    if request.method == 'POST':
        data = request.json
        rank_type = data.get('type')
        player = data.get('player')
        if rank_type == "global":
            return jsonify({"scores": display_ranking(), "current_player": player})
        elif rank_type == "day":
            return jsonify({"scores": display_ranking(filter_type="day"), "current_player": player})
        elif rank_type == "week":
            return jsonify({"scores": display_ranking(filter_type="week"), "current_player": player})
        elif rank_type == "player":
            return jsonify({"scores": display_ranking(filter_type="player", player=player), "current_player": player})
        elif rank_type == "multiplayer_1x1":
            return jsonify({"scores": display_multiplayer_ranking(mode="1x1"), "current_player": player})
        elif rank_type == "multiplayer_2x2":
            return jsonify({"scores": display_multiplayer_ranking(mode="2x2"), "current_player": player})
        elif rank_type == "tournament_1x1":
            return jsonify({"scores": display_multiplayer_ranking(mode="1x1", tournament_only=True), "current_player": player})
        elif rank_type == "tournament_2x2":
            return jsonify({"scores": display_multiplayer_ranking(mode="2x2", tournament_only=True), "current_player": player})
        elif rank_type == "history":
            return jsonify({"scores": display_match_history(), "current_player": player})
    return render_template('ranking.html')

@app.route('/online', methods=['GET', 'POST'])
def online():
    if request.method == 'POST':
        data = request.json
        player = data.get('player')
        session_id = data.get('session_id')
        mode = data.get('mode')
        difficulty = data.get('difficulty')
        rounds = data.get('rounds')

        valid, message = validate_unique_name(player, [])
        if not valid:
            return jsonify({"status": "error", "message": message})

        valid, rounds_val = get_rounds(rounds)
        if not valid:
            return jsonify({"status": "error", "message": rounds_val})

        max_number = get_difficulty(difficulty)
        game_state = game_states.get(session_id)
        if not game_state:
            game_state = {
                "session_id": session_id,
                "mode": mode,
                "max_number": max_number,
                "rounds": 1 if mode == "tournament_1x1" else rounds_val,
                "current_round": 1,
                "players": {},
                "scores": {},
                "numbers": {},
                "attempts": {},
                "hint_used": {},
                "current_player": None,
                "game_over": False,
                "tournament_phase": "semifinals" if mode == "tournament_1x1" else "rounds"
            }
            game_state["players"][player] = {"sid": None}
            game_state["scores"][player] = 0
            game_state["numbers"][player] = [random.randint(1, max_number) for _ in range(5)]
            game_state["attempts"][player] = []
            game_state["hint_used"][player] = False
            if mode == "2x2" or mode == "tournament_2x2":
                team = data.get('team')
                valid, message = validate_unique_name(team, [], is_team=True)
                if not valid:
                    return jsonify({"status": "error", "message": message})
                game_state["players"][player]["team"] = team
                game_state["scores"][team] = 0

            game_states[session_id] = game_state

        save_online_session(player, session_id, mode)
        return jsonify({"status": "start", "message": f"Conectado à sessão online {session_id}!", "session_id": session_id, "game_state": game_state})

    return render_template('online.html')

# WebSocket Handlers
@socketio.on('join_game')
def handle_join_game(data):
    session_id = data['session_id']
    player = data['player']
    game_state = game_states.get(session_id)
    if game_state and player in game_state['players']:
        game_state['players'][player]['sid'] = request.sid
        join_room(session_id)
        emit('game_message', {'status': 'joined', 'message': f'{player} entrou na sessão {session_id}!'}, room=session_id)
        if all(p['sid'] for p in game_state['players'].values()):
            game_state['current_player'] = list(game_state['players'].keys())[0]
            emit('game_start', {'message': f'Jogo iniciado! Vez de {game_state["current_player"]}.', 'current_player': game_state['current_player'], 'phase': game_state['tournament_phase']}, room=session_id)
    else:
        emit('game_message', {'status': 'error', 'message': 'Sessão ou jogador não encontrado!'})

@socketio.on('submit_guess')
def handle_submit_guess(data):
    session_id = data['session_id']
    player = data['player']
    guess = data['guess']
    game_state = game_states.get(session_id)
    if not game_state or player != game_state['current_player']:
        emit('game_message', {'status': 'error', 'message': 'Não é sua vez ou sessão inválida!'}, to=request.sid)
        return

    mode = game_state['mode']
    max_number = game_state['max_number']
    attempts = game_state['attempts'][player]
    hint_used = game_state['hint_used'][player]
    numbers = game_state['numbers'][player]

    result = play_round(player, numbers, max_number, attempts, hint_used, guess)
    game_state['attempts'][player] = attempts
    game_state['hint_used'][player] = result['hint_used']
    emit('game_message', {'status': result['status'], 'message': result['message'], 'player': player}, room=session_id)

    if result['status'] == 'correct':
        game_state['scores'][player] += result['score']
        if mode in ['2x2', 'tournament_2x2']:
            team = game_state['players'][player]['team']
            game_state['scores'][team] += result['score']
        game_state['attempts'][player] = []
        game_state['hint_used'][player] = False
        game_state['numbers'][player] = [random.randint(1, max_number) for _ in range(5)]

    players = list(game_state['players'].keys())
    current_idx = players.index(player)
    next_idx = (current_idx + 1) % len(players)
    game_state['current_player'] = players[next_idx]

    if all(len(game_state['attempts'][p]) == 0 for p in players):
        game_state['current_round'] += 1
        if game_state['current_round'] > game_state['rounds'] or (game_state['tournament_phase'] == 'final' and mode == 'tournament_1x1'):
            game_state['game_over'] = True
            if mode in ['1x1', 'tournament_1x1']:
                scores = {p: game_state['scores'][p] for p in players}
                winner = max(scores, key=scores.get)
                message = f"Jogo encerrado! {winner} venceu com {scores[winner]} pontos!" if scores[winner] > min(scores.values()) else "Empate!"
                if not game_state.get('training', False):
                    for p in players:
                        save_multiplayer_score(p, None, 1 if p == winner else 0, scores[p], is_tournament=mode == 'tournament_1x1')
            else:
                teams = {game_state['players'][p]['team'] for p in players}
                scores = {t: game_state['scores'][t] for t in teams}
                winner = max(scores, key=scores.get)
                message = f"Jogo encerrado! Equipe {winner} venceu com {scores[winner]} pontos!" if scores[winner] > min(scores.values()) else "Empate!"
                if not game_state.get('training', False):
                    for p in players:
                        team = game_state['players'][p]['team']
                        save_multiplayer_score(p, team, 1 if team == winner else 0, game_state['scores'][p], is_tournament=mode == 'tournament_2x2')
            emit('game_over', {'message': message, 'scores': game_state['scores'], 'phase': game_state['tournament_phase']}, room=session_id)
            return
        elif mode == 'tournament_1x1' and game_state['tournament_phase'] == 'semifinals':
            game_state['tournament_phase'] = 'final'
            winners = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)[:2]
            game_state['players'] = {p[0]: game_state['players'][p[0]] for p in winners}
            game_state['scores'] = {p[0]: 0 for p in winners}
            game_state['numbers'] = {p[0]: [random.randint(1, max_number) for _ in range(5)] for p in winners}
            game_state['attempts'] = {p[0]: [] for p in winners}
            game_state['hint_used'] = {p[0]: False for p in winners}
            game_state['current_round'] = 1
            emit('game_message', {'status': 'info', 'message': f"Iniciando a final: {winners[0][0]} vs {winners[1][0]}!", 'phase': 'final'}, room=session_id)

    emit('game_update', {'message': f'Vez de {game_state["current_player"]}.', 'current_player': game_state['current_player'], 'phase': game_state['tournament_phase']}, room=session_id)

@socketio.on('rematch')
def handle_rematch(data):
    session_id = data['session_id']
    game_state = game_states.get(session_id)
    if game_state:
        game_state['current_round'] = 1
        game_state['game_over'] = False
        for player in game_state['players']:
            game_state['scores'][player] = 0
            game_state['numbers'][player] = [random.randint(1, game_state['max_number']) for _ in range(5)]
            game_state['attempts'][player] = []
            game_state['hint_used'][player] = False
        if game_state['mode'] in ['2x2', 'tournament_2x2']:
            for team in set(game_state['players'][p]['team'] for p in game_state['players']):
                game_state['scores'][team] = 0
        game_state['current_player'] = list(game_state['players'].keys())[0]
        game_state['tournament_phase'] = 'semifinals' if game_state['mode'] == 'tournament_1x1' and len(game_state['players']) == 4 else 'rounds'
        emit('game_start', {'message': f'Revanche iniciada! Vez de {game_state["current_player"]}.', 'current_player': game_state['current_player'], 'phase': game_state['tournament_phase']}, room=session_id)
