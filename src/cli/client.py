import socketio
from rich.console import Console
from rich.prompt import Prompt

sio = socketio.Client()
console = Console()

@sio.event
def connect():
    console.print('[bold green]Conectado ao servidor![/bold green]')

@sio.event
def disconnect():
    console.print('[bold red]Desconectado do servidor![/bold red]')

@sio.on('game_message')
def on_message(data):
    console.print(f"[cyan]{data['message']}[/cyan]")

@sio.on('game_start')
def on_game_start(data):
    console.print(f"[bold magenta]{data['message']}[/bold magenta]")
    console.print(f"Sua vez, {data['current_player']}!")
    if data.get('phase'):
        console.print(f"Fase: {data['phase']}")

@sio.on('game_update')
def on_game_update(data):
    console.print(f"[bold magenta]{data['message']}[/bold magenta]")
    if sio.sid == data['current_player_sid']:
        guess = Prompt.ask("Sua jogada")
        sio.emit('submit_guess', {'guess': guess})

@sio.on('game_over')
def on_game_over(data):
    console.print(f"[bold green]{data['message']}[/bold green]")
    console.print("Placar final:")
    for player, score in data['scores'].items():
        console.print(f"{player}: {score}")
    sio.disconnect()

def run_client(player, session_id, mode, team, max_number, rounds, tournament):
    try:
        sio.connect('http://localhost:5000')
        sio.emit('join_game', {
            'player': player,
            'session_id': session_id,
            'mode': mode,
            'team': team,
            'max_number': max_number,
            'rounds': rounds,
            'tournament': tournament
        })
        sio.wait()
    except Exception as e:
        console.print(f"[red]Erro ao conectar ao servidor: {e}[/red]")
