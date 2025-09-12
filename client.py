import socket
import json
from rich.console import Console
from rich.prompt import Prompt
from cryptography.fernet import Fernet

console = Console()

class GameClient:
    def __init__(self, host='localhost', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.cipher = None
        self.console = Console()

    def send(self, data):
        if self.cipher:
            self.client.send(self.cipher.encrypt(json.dumps(data).encode('utf-8')))
        else:
            self.client.send(json.dumps(data).encode('utf-8'))

    def receive(self):
        data = self.client.recv(2048)
        if self.cipher:
            return json.loads(self.cipher.decrypt(data).decode('utf-8'))
        return json.loads(data.decode('utf-8'))

    def run(self, player, session_id, mode, team=None, difficulty=20, rounds=1, tournament=False):
        self.send({"player": player, "session_id": session_id, "mode": mode, "team": team})
        response = self.receive()
        if response['status'] == 'error':
            self.console.print(f"[red]{response['message']}[/red]")
            return
        
        self.cipher = Fernet(response['key'].encode())
        self.console.print(f"[green]{response['status']}: {response['player']} conectado![/green]")
        
        self.send({"action": "confirm", "confirmed": True})
        
        while True:
            try:
                data = self.receive()
                status = data.get('status')
                
                if status == 'confirmation':
                    self.console.print(f"[cyan]{data['message']}[/cyan]")
                
                elif status == 'start_round' or status == 'start_tournament_round':
                    self.console.print(f"[bold magenta]{data['message']}[/bold magenta]")
                    if status == 'start_tournament_round':
                        self.console.print(f"[cyan]Fase: {data['phase']}[/cyan]")
                        for match in data['matches']:
                            self.console.print(f"[cyan]Partida: {match[0]} vs {match[1]}[/cyan]")
                    
                    for i in range(1, 6):
                        self.console.print(f"\n[bold]Número {i} (1 a {difficulty})[/bold]")
                        for attempt in range(1, 4):
                            guess = Prompt.ask(f"Tentativa {attempt} (digite 'dica' para uma dica)")
                            self.send({"action": "guess", "number": i, "guess": guess})
                            response = self.receive()
                            self.console.print(f"[cyan]{response['message']}[/cyan]")
                            if response['status'] == 'correct':
                                break
                            elif response['status'] == 'error':
                                continue
                
                elif status == 'player_finished':
                    self.console.print(f"[cyan]{data['player']} terminou com {data['score']} pontos![/cyan]")
                
                elif status == 'end_round':
                    self.console.print(f"\n[bold green]Resultado da Rodada {data['round']}:[/bold green]")
                    for player, score in data['scores'].items():
                        self.console.print(f"{player}: {score} pontos")
                    if data.get('teams'):
                        for team, score in data['teams'].items():
                            self.console.print(f"{team}: {score} pontos")
                
                elif status == 'end_game':
                    self.console.print(f"\n[bold green]{data['message']}[/bold green]")
                    for player, score in data['scores'].items():
                        self.console.print(f"{player}: {score} pontos")
                    if data.get('teams'):
                        for team, score in data['teams'].items():
                            self.console.print(f"{team}: {score} pontos")
                
                elif status == 'rematch_prompt':
                    self.console.print(f"[cyan]{data['message']}[/cyan]")
                    rematch = Prompt.ask("Deseja revanche? (s/n)", choices=["s", "n"], default="n")
                    self.send({"action": "rematch", "confirmed": rematch == 's'})
                
                elif status == 'error':
                    self.console.print(f"[red]{data['message']}[/red]")
            
            except Exception as e:
                self.console.print(f"[red]Erro: {e}[/red]")
                break
        
        self.client.close()

if __name__ == "__main__":
    player = Prompt.ask("Digite seu nome")
    session_id = Prompt.ask("Digite o ID da sessão")
    mode = Prompt.ask("Escolha o modo (1x1/2x2)", choices=["1x1", "2x2"], default="1x1")
    team = Prompt.ask("Digite o nome da equipe (ou deixe em branco para 1x1)", default=None) if mode == "2x2" else None
    client = GameClient()
    client.run(player, session_id, mode, team)