import random
from rich.console import Console
from rich.prompt import Prompt
from src.database import (
    save_score,
    fetch_scores,
    save_multiplayer_score,
    fetch_multiplayer_scores,
    save_wifi_player,
    remove_wifi_player,
    fetch_wifi_players,
    fetch_match_history,
)
from src.game import (
    get_badge,
    validate_unique_name,
    get_rounds,
    get_difficulty,
    play_round,
)
from .client import run_client

console = Console()

def menu():
    console.clear()
    console.print("[bold green]🎲 Adivinhe o Número: Arena dos Números 🎮[/bold green]", style="cyan")
    console.print("🌟 [1] Singleplayer - Desafie os números sozinho!")
    console.print("⚔️ [2] Multiplayer 1x1 - Duelo direto!")
    console.print("🤝 [3] Multiplayer 2x2 - Força em equipe!")
    console.print("🏆 [4] Torneio 2x2 - A glória espera!")
    console.print("🥇 [5] Torneio 1x1 - Prove quem é o melhor!")
    console.print("💪 [6] Modo Treino - Afie suas habilidades!")
    console.print("📡 [7] Gerenciar Jogadores Wi-Fi - Controle a rede!")
    console.print("📊 [8] Ver Ranking - Veja os campeões!")
    console.print("🌐 [9] Jogar Online - Desafie o mundo!")
    console.print("🚪 [10] Sair - Até a próxima aventura!")
    return Prompt.ask("[bold cyan]Escolha sua aventura[/bold cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

def show_rank_menu():
    console.print("[bold cyan]🏆 Templo dos Rankings 🏆[/bold cyan]", style="cyan")
    console.print("📈 [1] Ranking Global (Singleplayer)")
    console.print("🌞 [2] Ranking do Dia")
    console.print("📅 [3] Ranking da Semana")
    console.print("👤 [4] Meu Ranking")
    console.print("⚔️ [5] Ranking Multiplayer 1x1")
    console.print("🤝 [6] Ranking Multiplayer 2x2")
    console.print("🏆 [7] Ranking Torneio 1x1")
    console.print("🏅 [8] Ranking Torneio 2x2")
    console.print("📜 [9] Histórico de Partidas")
    console.print("🔙 [10] Voltar")
    return Prompt.ask("[bold cyan]Escolha o ranking[/bold cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

def show_train_menu():
    console.print("[bold cyan]💪 Campo de Treinamento 💪[/bold cyan]", style="cyan")
    console.print("🎯 [1] Treino Singleplayer")
    console.print("⚔️ [2] Treino Multiplayer 1x1")
    console.print("🤝 [3] Treino Multiplayer 2x2")
    console.print("🔙 [4] Voltar")
    return Prompt.ask("[bold cyan]Escolha o treino[/bold cyan]", choices=["1", "2", "3", "4"])

def show_online_menu():
    console.print("[bold cyan]🌐 Arena Online Global 🌐[/bold cyan]", style="cyan")
    console.print("⚔️ [1] Multiplayer 1x1")
    console.print("🤝 [2] Multiplayer 2x2")
    console.print("🏆 [3] Torneio 1x1")
    console.print("🏅 [4] Torneio 2x2")
    console.print("🔙 [5] Voltar")
    return Prompt.ask("[bold cyan]Escolha o modo online[/bold cyan]", choices=["1", "2", "3", "4", "5"])

def display_ranking(filter_type=None, player=None):
    scores = fetch_scores(filter_type, player)
    # This should be formatted and printed to the console
    console.print(scores)

def display_multiplayer_ranking(mode="1x1", tournament_only=False):
    scores = fetch_multiplayer_scores(mode, tournament_only)
    # This should be formatted and printed to the console
    console.print(scores)

def display_match_history():
    history = fetch_match_history()
    # This should be formatted and printed to the console
    console.print(history)

def play_singleplayer_cli(save_results=True):
    name, _ = validate_unique_name(Prompt.ask("Digite seu nome, desafiante"), [], is_team=False)
    max_number = get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    secret_number = random.randint(1, max_number)
    console.print(f"[bold blue]🎯 {name}, enfrente o desafio! Adivinhe o número entre 1 e {max_number}! Você tem 6 tentativas.[/bold blue]")
    
    hint_used = False
    for attempts in range(1, 7):
        guess = Prompt.ask(f"[bold yellow]Tentativa {attempts}/6 (digite 'dica' para uma pista)[/bold yellow]")
        if guess.lower() == 'dica' and not hint_used:
            hint_used = True
            console.print(f"[cyan]💡 Dica: O número é {'par' if secret_number % 2 == 0 else 'ímpar'}![/cyan]")
            continue
        try:
            guess = int(guess)
        except ValueError:
            console.print("[red]⚠️ Insira um número inteiro ou 'dica'![/red]")
            continue

        if guess < secret_number:
            console.print("[yellow]🔽 Muito baixo![/yellow]")
        elif guess > secret_number:
            console.print("[yellow]🔼 Muito alto![/yellow]")
        else:
            final_attempts = attempts - (1 if hint_used else 0)
            console.print(f"[green]🎉 Parabéns, {name}! Você acertou em {final_attempts} tentativas![/green]")
            if save_results and final_attempts > 0:
                save_score(name, final_attempts)
            break
    else:
        console.print(f"[red]😔 Não foi dessa vez, {name}. O número era {secret_number}.[/red]")

def play_round_cli(player, numbers, max_number):
    score = 0
    hint_used = False
    for i, secret_number in enumerate(numbers, 1):
        console.print(f"\n[bold]🔢 Número {i} (1 a {max_number}) - 3 tentativas[/bold]")
        for attempt in range(1, 4):
            guess = Prompt.ask(f"[bold yellow]{player}, tentativa {attempt}/3 (digite 'dica' para uma pista)[/bold yellow]")
            if guess.lower() == 'dica' and not hint_used:
                hint_used = True
                console.print(f"[cyan]💡 Dica: O número é {'par' if secret_number % 2 == 0 else 'ímpar'}![/cyan]")
                continue
            try:
                guess = int(guess)
            except ValueError:
                console.print("[red]⚠️ Insira um número inteiro ou 'dica'![/red]")
                continue
            
            if guess < secret_number:
                console.print("[yellow]🔽 Muito baixo![/yellow]")
            elif guess > secret_number:
                console.print("[yellow]🔼 Muito alto![/yellow]")
            else:
                points = 4 - attempt - (1 if hint_used else 0)
                points = max(1, points)
                console.print(f"[green]🎯 Acertou o número {i}! (+{points} pontos)[/green]")
                score += points
                break
        else:
            console.print(f"[red]❌ Não acertou! O número era {secret_number}.[/red]")
        hint_used = False
    return score

def play_multiplayer_1x1_cli(save_results=True, rematch=False, prev_players=None, prev_max_number=None, prev_rounds=None):
    max_number = prev_max_number if rematch else get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    rounds, _ = prev_rounds if rematch else get_rounds(Prompt.ask("[bold cyan]Digite o número de rodadas (1-5)[/bold cyan]", default="3"))
    used_names = prev_players if rematch else []
    
    if not rematch:
        player1, _ = validate_unique_name(Prompt.ask("Digite o nome do Desafiante 1"), used_names, is_team=False)
        used_names.append(player1)
        player2, _ = validate_unique_name(Prompt.ask("Digite o nome do Desafiante 2"), used_names, is_team=False)
    else:
        player1, player2 = prev_players
    
    console.print(f"\n[bold blue]⚔️ Duelo 1x1: {player1} vs {player2} ({rounds} rodadas)[/bold blue]")
    console.print(f"[cyan]Regras: 3 tentativas por número (5 números, 1-{max_number}). Pontuação: 3 pontos (1ª tentativa), 2 pontos (2ª), 1 ponto (3ª). Dica custa 1 ponto.[/cyan]")
    
    score_p1_total = 0
    score_p2_total = 0
    
    for round_num in range(1, rounds + 1):
        console.print(f"\n[bold magenta]🔥 Rodada {round_num}/{rounds} 🔥[/bold magenta]")
        numbers_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_p2 = [random.randint(1, max_number) for _ in range(5)]
        
        console.print(f"\n[bold cyan]🛡️ {player1}, sua vez![/bold cyan]")
        score_p1 = play_round_cli(player1, numbers_p1, max_number)
        
        console.print(f"\n[bold cyan]🛡️ {player2}, sua vez![/bold cyan]")
        score_p2 = play_round_cli(player2, numbers_p2, max_number)
        
        score_p1_total += score_p1
        score_p2_total += score_p2
        
        console.print(f"\n[bold green]📊 Resultado da Rodada {round_num}:[/bold green]")
        console.print(f"{player1}: {score_p1} pontos")
        console.print(f"{player2}: {score_p2} pontos")
        
        if save_results:
            if score_p1 > score_p2:
                save_multiplayer_score(player1, None, 1, score_p1)
                save_multiplayer_score(player2, None, 0, score_p2)
            elif score_p2 > score_p1:
                save_multiplayer_score(player1, None, 0, score_p1)
                save_multiplayer_score(player2, None, 1, score_p2)
            else:
                save_multiplayer_score(player1, None, 0, score_p1)
                save_multiplayer_score(player2, None, 0, score_p2)
    
    console.print(f"\n[bold green]🏁 Resultado Final:[/bold green]")
    console.print(f"{player1}: {score_p1_total} pontos")
    console.print(f"{player2}: {score_p2_total} pontos")
    
    if score_p1_total > score_p2_total:
        console.print(f"[green]🎉 {player1} domina a Arena![/green]")
    elif score_p2_total > score_p1_total:
        console.print(f"[green]🎉 {player2} domina a Arena![/green]")
    else:
        console.print("[yellow]⚖️ Empate épico![/yellow]")
    
    if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
        console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
        play_multiplayer_1x1_cli(save_results, rematch=True, prev_players=[player1, player2], prev_max_number=max_number, prev_rounds=rounds)

def play_multiplayer_2x2_cli(save_results=True, rematch=False, prev_teams=None, prev_max_number=None, prev_rounds=None):
    max_number = prev_max_number if rematch else get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    rounds, _ = prev_rounds if rematch else get_rounds(Prompt.ask("[bold cyan]Digite o número de rodadas (1-5)[/bold cyan]", default="3"))
    used_names = []
    
    if not rematch:
        team1_name, _ = validate_unique_name(Prompt.ask("Digite o nome da Equipe 1"), [], is_team=True)
        team1_p1, _ = validate_unique_name(f"Digite o nome do Guerreiro 1 da {team1_name}", used_names, is_team=False)
        used_names.append(team1_p1)
        team1_p2, _ = validate_unique_name(f"Digite o nome do Guerreiro 2 da {team1_name}", used_names, is_team=False)
        used_names.append(team1_p2)
        
        team2_name, _ = validate_unique_name(Prompt.ask("Digite o nome da Equipe 2"), [team1_name], is_team=True)
        team2_p1, _ = validate_unique_name(f"Digite o nome do Guerreiro 1 da {team2_name}", used_names, is_team=False)
        used_names.append(team2_p1)
        team2_p2, _ = validate_unique_name(f"Digite o nome do Guerreiro 2 da {team2_name}", used_names, is_team=False)
    else:
        team1_name, team1_p1, team1_p2, team2_name, team2_p1, team2_p2 = prev_teams
        used_names.extend([team1_p1, team1_p2, team2_p1, team2_p2])
    
    console.print(f"\n[bold blue]🤝 Batalha 2x2: {team1_name} vs {team2_name} ({rounds} rodadas)[/bold blue]")
    console.print(f"[cyan]Regras: 3 tentativas por número (5 números, 1-{max_number}). Pontuação: 3 pontos (1ª tentativa), 2 pontos (2ª), 1 ponto (3ª). Dica custa 1 ponto.[/cyan]")
    
    team1_total_score = 0
    team2_total_score = 0
    
    for round_num in range(1, rounds + 1):
        console.print(f"\n[bold magenta]🔥 Rodada {round_num}/{rounds} 🔥[/bold magenta]")
        
        numbers_t1_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t1_p2 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p2 = [random.randint(1, max_number) for _ in range(5)]
        
        team1_round_score = 0
        team2_round_score = 0
        
        console.print(f"\n[bold cyan]🛡️ {team1_name}, ao combate![/bold cyan]")
        console.print(f"\n[bold]{team1_p1}, sua vez![/bold]")
        score_t1_p1 = play_round_cli(team1_p1, numbers_t1_p1, max_number)
        team1_round_score += score_t1_p1
        console.print(f"\n[bold]{team1_p2}, sua vez![/bold]")
        score_t1_p2 = play_round_cli(team1_p2, numbers_t1_p2, max_number)
        team1_round_score += score_t1_p2
        
        console.print(f"\n[bold cyan]🛡️ {team2_name}, ao combate![/bold cyan]")
        console.print(f"\n[bold]{team2_p1}, sua vez![/bold]")
        score_t2_p1 = play_round_cli(team2_p1, numbers_t2_p1, max_number)
        team2_round_score += score_t2_p1
        console.print(f"\n[bold]{team2_p2}, sua vez![/bold]")
        score_t2_p2 = play_round_cli(team2_p2, numbers_t2_p2, max_number)
        team2_round_score += score_t2_p2
        
        team1_total_score += team1_round_score
        team2_total_score += team2_round_score
        
        console.print(f"\n[bold green]📊 Resultado da Rodada {round_num}:[/bold green]")
        console.print(f"{team1_name}: {team1_round_score} pontos ({team1_p1}: {score_t1_p1}, {team1_p2}: {score_t1_p2})")
        console.print(f"{team2_name}: {team2_round_score} pontos ({team2_p1}: {score_t2_p1}, {team2_p2}: {score_t2_p2})")
        
        if save_results:
            if team1_round_score > team2_round_score:
                save_multiplayer_score(team1_p1, team1_name, 1, score_t1_p1)
                save_multiplayer_score(team1_p2, team1_name, 1, score_t1_p2)
                save_multiplayer_score(team2_p1, team2_name, 0, score_t2_p1)
                save_multiplayer_score(team2_p2, team2_name, 0, score_t2_p2)
            elif team2_round_score > team1_round_score:
                save_multiplayer_score(team1_p1, team1_name, 0, score_t1_p1)
                save_multiplayer_score(team1_p2, team1_name, 0, score_t1_p2)
                save_multiplayer_score(team2_p1, team2_name, 1, score_t2_p1)
                save_multiplayer_score(team2_p2, team2_name, 1, score_t2_p2)
            else:
                save_multiplayer_score(team1_p1, team1_name, 0, score_t1_p1)
                save_multiplayer_score(team1_p2, team1_name, 0, score_t1_p2)
                save_multiplayer_score(team2_p1, team2_name, 0, score_t2_p1)
                save_multiplayer_score(team2_p2, team2_name, 0, score_t2_p2)
    
    console.print(f"\n[bold green]🏁 Resultado Final:[/bold green]")
    console.print(f"{team1_name}: {team1_total_score} pontos")
    console.print(f"{team2_name}: {team2_total_score} pontos")
    
    if team1_total_score > team2_total_score:
        console.print(f"[green]🎉 {team1_name} domina a Arena![/green]")
    elif team2_total_score > team1_total_score:
        console.print(f"[green]🎉 {team2_name} domina a Arena![/green]")
    else:
        console.print("[yellow]⚖️ Empate épico![/yellow]")
    
    if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
        console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
        play_multiplayer_2x2_cli(save_results, rematch=True, prev_teams=[team1_name, team1_p1, team1_p2, team2_name, team1_p1, team2_p2], prev_max_number=max_number, prev_rounds=rounds)

def simulate_wifi_players_cli(max_players, is_team=False):
    console.print(f"\n[bold blue]📡 Rede Wi-Fi: {'Seleção de Equipes' if is_team else 'Seleção de Jogadores'}[/bold blue]")
    console.print(f"[cyan]Jogadores disponíveis: {', '.join(fetch_wifi_players()) or 'Nenhum'}[/cyan]")
    console.print(f"[yellow]Selecione até {max_players} {'equipes' if is_team else 'jogadores'}. Digite 'novo' para adicionar, 'remover' para remover, ou 'fim' para encerrar.[/yellow]")
    
    players = []
    teams = []
    used_names = []
    
    while len(players) < max_players * (2 if is_team else 1):
        name = Prompt.ask(f"[bold cyan]Selecione {'a Equipe' if is_team else 'o Jogador'} {len(teams) + 1 if is_team else len(players) + 1} (ou 'novo', 'remover', 'fim')[/bold cyan]")
        if name.lower() == 'fim':
            break
        elif name.lower() == 'novo':
            if is_team:
                team_name, _ = validate_unique_name(Prompt.ask("Digite o nome da nova equipe"), used_names, is_team=True)
                used_names.append(team_name)
                p1, _ = validate_unique_name(f"Digite o nome do Jogador 1 da {team_name}", used_names, is_team=False, is_wifi=True)
                save_wifi_player(p1)
                used_names.append(p1)
                p2, _ = validate_unique_name(f"Digite o nome do Jogador 2 da {team_name}", used_names, is_team=False, is_wifi=True)
                save_wifi_player(p2)
                used_names.append(p2)
                teams.append((team_name, p1, p2))
            else:
                new_name, _ = validate_unique_name(Prompt.ask("Digite o nome do novo jogador"), used_names, is_team=False, is_wifi=True)
                save_wifi_player(new_name)
                console.print(f"[green]✅ Jogador {new_name} adicionado à rede Wi-Fi![/green]")
            continue
        elif name.lower() == 'remover':
            player_to_remove = Prompt.ask("[bold cyan]Digite o nome do jogador a remover[/bold cyan]")
            if player_to_remove in fetch_wifi_players():
                remove_wifi_player(player_to_remove)
                console.print(f"[green]✅ Jogador {player_to_remove} removido da rede Wi-Fi![/green]")
            else:
                console.print("[red]⚠️ Jogador não encontrado na rede Wi-Fi![/red]")
            continue
        if is_team:
            team_found = False
            for team_name, p1, p2 in teams:
                if team_name == name:
                    console.print("[red]⚠️ Esta equipe já foi selecionada![/red]")
                    team_found = True
                    break
            if team_found:
                continue
            found_players = [p for p in fetch_wifi_players() if p.startswith(name + "_")]
            if len(found_players) != 2:
                console.print("[red]⚠️ Equipe não encontrada ou incompleta na rede Wi-Fi![/red]")
                continue
            if Prompt.ask(f"[bold cyan]Confirmar participação da equipe {name}? (s/n)[/bold cyan]", choices=["s", "n"], default="s") == "n":
                console.print(f"[yellow]🚫 Equipe {name} recusou o convite.[/yellow]")
                continue
            teams.append((name, found_players[0], found_players[1]))
            players.extend(found_players)
            used_names.extend(found_players)
        else:
            if name not in fetch_wifi_players():
                console.print("[red]⚠️ Jogador não está na rede Wi-Fi! Use 'novo' para adicionar.[/red]")
                continue
            if name in used_names:
                console.print("[red]⚠️ Este jogador já foi selecionado! Escolha outro.[/red]")
                continue
            if Prompt.ask(f"[bold cyan]Confirmar participação de {name}? (s/n)[/bold cyan]", choices=["s", "n"], default="s") == "n":
                console.print(f"[yellow]🚫 Jogador {name} recusou o convite.[/yellow]")
                continue
            players.append(name)
            used_names.append(name)
    
    if len(players) < 2 * (2 if is_team else 1):
        console.print(f"[red]⚠️ É necessário pelo menos 2 {'equipes' if is_team else 'jogadores'} para iniciar o torneio![/red]")
        return None
    return teams if is_team else players

def play_tournament_1x1_cli(save_results=True, rematch=False, prev_players=None, prev_max_number=None, prev_rounds=None):
    max_number = prev_max_number if rematch else get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    rounds, _ = prev_rounds if rematch else get_rounds(Prompt.ask("[bold cyan]Digite o número de rodadas (1-5)[/bold cyan]", default="3")) if len(prev_players or []) < 4 else (1, None)
    players = prev_players if rematch else simulate_wifi_players_cli(max_players=4)
    
    if not players:
        return
    
    console.print(f"\n[bold blue]🏆 Torneio 1x1: {', '.join(players)} ({'Chaves' if len(players) == 4 else f'{rounds} rodadas'})[/bold blue]")
    console.print(f"[cyan]Regras: 3 tentativas por número (5 números, 1-{max_number}). Pontuação: 3 pontos (1ª tentativa), 2 pontos (2ª), 1 ponto (3ª). Dica custa 1 ponto.[/cyan]")
    
    if len(players) == 4:
        console.print("\n[bold magenta]🔥 Semifinais 🔥[/bold magenta]")
        semi1 = (players[0], players[1])
        semi2 = (players[2], players[3])
        
        console.print(f"\n[bold cyan]⚔️ Semifinal 1: {semi1[0]} vs {semi1[1]}[/bold cyan]")
        numbers_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_p2 = [random.randint(1, max_number) for _ in range(5)]
        score_p1 = play_round_cli(semi1[0], numbers_p1, max_number)
        score_p2 = play_round_cli(semi1[1], numbers_p2, max_number)
        console.print(f"\n[bold green]📊 Resultado: {semi1[0]}: {score_p1} pontos, {semi1[1]}: {score_p2} pontos[/bold green]")
        winner1 = semi1[0] if score_p1 > score_p2 else semi1[1]
        if save_results:
            save_multiplayer_score(semi1[0], None, 1 if score_p1 > score_p2 else 0, score_p1, is_tournament=1)
            save_multiplayer_score(semi1[1], None, 1 if score_p2 > score_p1 else 0, score_p2, is_tournament=1)
        
        console.print(f"\n[bold cyan]⚔️ Semifinal 2: {semi2[0]} vs {semi2[1]}[/bold cyan]")
        numbers_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_p2 = [random.randint(1, max_number) for _ in range(5)]
        score_p1 = play_round_cli(semi2[0], numbers_p1, max_number)
        score_p2 = play_round_cli(semi2[1], numbers_p2, max_number)
        console.print(f"\n[bold green]📊 Resultado: {semi2[0]}: {score_p1} pontos, {semi2[1]}: {score_p2} pontos[/bold green]")
        winner2 = semi2[0] if score_p1 > score_p2 else semi2[1]
        if save_results:
            save_multiplayer_score(semi2[0], None, 1 if score_p1 > score_p2 else 0, score_p1, is_tournament=1)
            save_multiplayer_score(semi2[1], None, 1 if score_p2 > score_p1 else 0, score_p2, is_tournament=1)
        
        console.print(f"\n[bold magenta]🏅 Final: {winner1} vs {winner2} 🏅[/bold magenta]")
        numbers_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_p2 = [random.randint(1, max_number) for _ in range(5)]
        score_p1 = play_round_cli(winner1, numbers_p1, max_number)
        score_p2 = play_round_cli(winner2, numbers_p2, max_number)
        console.print(f"\n[bold green]🏁 Resultado Final do Torneio:[/bold green]")
        console.print(f"{winner1}: {score_p1} pontos")
        console.print(f"{winner2}: {score_p2} pontos")
        if score_p1 > score_p2:
            console.print(f"[green]🎉 {winner1} é o campeão do torneio![/green]")
            if save_results:
                save_multiplayer_score(winner1, None, 1, score_p1, is_tournament=1)
                save_multiplayer_score(winner2, None, 0, score_p2, is_tournament=1)
        elif score_p2 > score_p1:
            console.print(f"[green]🎉 {winner2} é o campeão do torneio![/green]")
            if save_results:
                save_multiplayer_score(winner1, None, 0, score_p1, is_tournament=1)
                save_multiplayer_score(winner2, None, 1, score_p2, is_tournament=1)
        else:
            console.print(f"[yellow]⚖️ Empate entre {winner1} e {winner2}![/yellow]")
            if save_results:
                save_multiplayer_score(winner1, None, 0, score_p1, is_tournament=1)
                save_multiplayer_score(winner2, None, 0, score_p2, is_tournament=1)
        
        if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
            console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
            play_tournament_1x1_cli(save_results, rematch=True, prev_players=players, prev_max_number=max_number, prev_rounds=rounds)
    else:
        player_scores = {player: 0 for player in players}
        for round_num in range(1, rounds + 1):
            console.print(f"\n[bold magenta]🔥 Rodada {round_num}/{rounds} 🔥[/bold magenta]")
            round_scores = {}
            
            for player in players:
                console.print(f"\n[bold cyan]🛡️ {player}, sua vez![/bold cyan]")
                numbers = [random.randint(1, max_number) for _ in range(5)]
                score = play_round_cli(player, numbers, max_number)
                round_scores[player] = score
            
            console.print(f"\n[bold green]📊 Resultado da Rodada {round_num}:[/bold green]")
            for player, score in round_scores.items():
                console.print(f"{player}: {score} pontos")
                player_scores[player] += score
            
            max_score = max(round_scores.values())
            winners = [p for p, s in round_scores.items() if s == max_score]
            if save_results:
                for player in players:
                    wins = 1 if player in winners and len(winners) == 1 else 0
                    save_multiplayer_score(player, None, wins, round_scores[player], is_tournament=1)
        
        console.print(f"\n[bold green]🏁 Resultado Final do Torneio:[/bold green]")
        for player, total_score in player_scores.items():
            console.print(f"{player}: {total_score} pontos")
        
        max_total_score = max(player_scores.values())
        winners = [p for p, s in player_scores.items() if s == max_total_score]
        if len(winners) == 1:
            console.print(f"[green]🎉 {winners[0]} é o campeão do torneio![/green]")
        else:
            console.print(f"[yellow]⚖️ Empate entre {', '.join(winners)}![/yellow]")
        
        if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
            console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
            play_tournament_1x1_cli(save_results, rematch=True, prev_players=players, prev_max_number=max_number, prev_rounds=rounds)

def play_tournament_2x2_cli(save_results=True, rematch=False, prev_teams=None, prev_max_number=None, prev_rounds=None):
    max_number = prev_max_number if rematch else get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    rounds, _ = prev_rounds if rematch else get_rounds(Prompt.ask("[bold cyan]Digite o número de rodadas (1-5)[/bold cyan]", default="3")) if len(prev_teams or []) < 4 else (1, None)
    teams = prev_teams if rematch else simulate_wifi_players_cli(max_players=4, is_team=True)
    
    if not teams:
        return
    
    console.print(f"\n[bold blue]🏅 Torneio 2x2: {', '.join([t[0] for t in teams])} ({'Chaves' if len(teams) == 4 else f'{rounds} rodadas'})[/bold blue]")
    console.print(f"[cyan]Regras: 3 tentativas por número (5 números, 1-{max_number}). Pontuação: 3 pontos (1ª tentativa), 2 pontos (2ª), 1 ponto (3ª). Dica custa 1 ponto.[/cyan]")
    
    if len(teams) == 4:
        console.print("\n[bold magenta]🔥 Semifinais 🔥[/bold magenta]")
        semi1 = (teams[0], teams[1])
        semi2 = (teams[2], teams[3])
        
        console.print(f"\n[bold cyan]⚔️ Semifinal 1: {semi1[0][0]} vs {semi1[1][0]}[/bold cyan]")
        team1_score = 0
        team2_score = 0
        numbers_t1_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t1_p2 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p2 = [random.randint(1, max_number) for _ in range(5)]
        
        console.print(f"\n[bold]{semi1[0][0]}: {semi1[0][1]}[/bold]")
        score_t1_p1 = play_round_cli(semi1[0][1], numbers_t1_p1, max_number)
        team1_score += score_t1_p1
        console.print(f"\n[bold]{semi1[0][0]}: {semi1[0][2]}[/bold]")
        score_t1_p2 = play_round_cli(semi1[0][2], numbers_t1_p2, max_number)
        team1_score += score_t1_p2
        console.print(f"\n[bold]{semi1[1][0]}: {semi1[1][1]}[/bold]")
        score_t2_p1 = play_round_cli(semi1[1][1], numbers_t2_p1, max_number)
        team2_score += score_t2_p1
        console.print(f"\n[bold]{semi1[1][0]}: {semi1[1][2]}[/bold]")
        score_t2_p2 = play_round_cli(semi1[1][2], numbers_t2_p2, max_number)
        team2_score += score_t2_p2
        
        console.print(f"\n[bold green]📊 Resultado: {semi1[0][0]}: {team1_score} pontos, {semi1[1][0]}: {team2_score} pontos[/bold green]")
        winner1 = semi1[0] if team1_score > team2_score else semi1[1]
        if save_results:
            save_multiplayer_score(semi1[0][1], semi1[0][0], 1 if team1_score > team2_score else 0, score_t1_p1, is_tournament=1)
            save_multiplayer_score(semi1[0][2], semi1[0][0], 1 if team1_score > team2_score else 0, score_t1_p2, is_tournament=1)
            save_multiplayer_score(semi1[1][1], semi1[1][0], 1 if team2_score > team1_score else 0, score_t2_p1, is_tournament=1)
            save_multiplayer_score(semi1[1][2], semi1[1][0], 1 if team2_score > team1_score else 0, score_t2_p2, is_tournament=1)
        
        console.print(f"\n[bold cyan]⚔️ Semifinal 2: {semi2[0][0]} vs {semi2[1][0]}[/bold cyan]")
        team1_score = 0
        team2_score = 0
        numbers_t1_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t1_p2 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p2 = [random.randint(1, max_number) for _ in range(5)]
        
        console.print(f"\n[bold]{semi2[0][0]}: {semi2[0][1]}[/bold]")
        score_t1_p1 = play_round_cli(semi2[0][1], numbers_t1_p1, max_number)
        team1_score += score_t1_p1
        console.print(f"\n[bold]{semi2[0][0]}: {semi2[0][2]}[/bold]")
        score_t1_p2 = play_round_cli(semi2[0][2], numbers_t1_p2, max_number)
        team1_score += score_t1_p2
        
        console.print(f"\n[bold]{semi2[1][0]}: {semi2[1][1]}[/bold]")
        score_t2_p1 = play_round_cli(semi2[1][1], numbers_t2_p1, max_number)
        team2_score += score_t2_p1
        console.print(f"\n[bold]{semi2[1][0]}: {semi2[1][2]}[/bold]")
        score_t2_p2 = play_round_cli(semi2[1][2], numbers_t2_p2, max_number)
        team2_score += score_t2_p2
        
        console.print(f"\n[bold green]📊 Resultado: {semi2[0][0]}: {team1_score} pontos, {semi2[1][0]}: {team2_score} pontos[/bold green]")
        winner2 = semi2[0] if team1_score > team2_score else semi2[1]
        if save_results:
            save_multiplayer_score(semi2[0][1], semi2[0][0], 1 if team1_score > team2_score else 0, score_t1_p1, is_tournament=1)
            save_multiplayer_score(semi2[0][2], semi2[0][0], 1 if team1_score > team2_score else 0, score_t1_p2, is_tournament=1)
            save_multiplayer_score(semi2[1][1], semi2[1][0], 1 if team2_score > team1_score else 0, score_t2_p1, is_tournament=1)
            save_multiplayer_score(semi2[1][2], semi2[1][0], 1 if team2_score > team1_score else 0, score_t2_p2, is_tournament=1)
        
        console.print(f"\n[bold magenta]🏅 Final: {winner1[0]} vs {winner2[0]} 🏅[/bold magenta]")
        team1_score = 0
        team2_score = 0
        numbers_t1_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t1_p2 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p1 = [random.randint(1, max_number) for _ in range(5)]
        numbers_t2_p2 = [random.randint(1, max_number) for _ in range(5)]
        
        console.print(f"\n[bold]{winner1[0]}: {winner1[1]}[/bold]")
        score_t1_p1 = play_round_cli(winner1[1], numbers_t1_p1, max_number)
        team1_score += score_t1_p1
        console.print(f"\n[bold]{winner1[0]}: {winner1[2]}[/bold]")
        score_t1_p2 = play_round_cli(winner1[2], numbers_t1_p2, max_number)
        team1_score += score_t1_p2
        
        console.print(f"\n[bold]{winner2[0]}: {winner2[1]}[/bold]")
        score_t2_p1 = play_round_cli(winner2[1], numbers_t2_p1, max_number)
        team2_score += score_t2_p1
        console.print(f"\n[bold]{winner2[0]}: {winner2[2]}[/bold]")
        score_t2_p2 = play_round_cli(winner2[2], numbers_t2_p2, max_number)
        team2_score += score_t2_p2
        
        console.print(f"\n[bold green]🏁 Resultado Final do Torneio:[/bold green]")
        console.print(f"{winner1[0]}: {team1_score} pontos")
        console.print(f"{winner2[0]}: {team2_score} pontos")
        if team1_score > team2_score:
            console.print(f"[green]🎉 {winner1[0]} é a equipe campeã![/green]")
            if save_results:
                save_multiplayer_score(winner1[1], winner1[0], 1, score_t1_p1, is_tournament=1)
                save_multiplayer_score(winner1[2], winner1[0], 1, score_t1_p2, is_tournament=1)
                save_multiplayer_score(winner2[1], winner2[0], 0, score_t2_p1, is_tournament=1)
                save_multiplayer_score(winner2[2], winner2[0], 0, score_t2_p2, is_tournament=1)
        elif team2_score > team1_score:
            console.print(f"[green]🎉 {winner2[0]} é a equipe campeã![/green]")
            if save_results:
                save_multiplayer_score(winner1[1], winner1[0], 0, score_t1_p1, is_tournament=1)
                save_multiplayer_score(winner1[2], winner1[0], 0, score_t1_p2, is_tournament=1)
                save_multiplayer_score(winner2[1], winner2[0], 1, score_t2_p1, is_tournament=1)
                save_multiplayer_score(winner2[2], winner2[0], 1, score_t2_p2, is_tournament=1)
        else:
            console.print(f"[yellow]⚖️ Empate entre {winner1[0]} e {winner2[0]}![/yellow]")
            if save_results:
                save_multiplayer_score(winner1[1], winner1[0], 0, score_t1_p1, is_tournament=1)
                save_multiplayer_score(winner1[2], winner1[0], 0, score_t1_p2, is_tournament=1)
                save_multiplayer_score(winner2[1], winner2[0], 0, score_t2_p1, is_tournament=1)
                save_multiplayer_score(winner2[2], winner2[0], 0, score_t2_p2, is_tournament=1)
        
        if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
            console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
            play_tournament_2x2_cli(save_results, rematch=True, prev_teams=teams, prev_max_number=max_number, prev_rounds=rounds)
    else:
        team_scores = {team[0]: 0 for team in teams}
        for round_num in range(1, rounds + 1):
            console.print(f"\n[bold magenta]🔥 Rodada {round_num}/{rounds} 🔥[/bold magenta]")
            round_scores = {}
            
            for team_name, p1, p2 in teams:
                console.print(f"\n[bold cyan]🛡️ {team_name}, ao combate![/bold cyan]")
                numbers_p1 = [random.randint(1, max_number) for _ in range(5)]
                numbers_p2 = [random.randint(1, max_number) for _ in range(5)]
                
                console.print(f"\n[bold]{p1}[/bold]")
                score_p1 = play_round_cli(p1, numbers_p1, max_number)
                console.print(f"\n[bold]{p2}[/bold]")
                score_p2 = play_round_cli(p2, numbers_p2, max_number)
                
                round_scores[team_name] = score_p1 + score_p2
            
            console.print(f"\n[bold green]📊 Resultado da Rodada {round_num}:[/bold green]")
            for team_name, score in round_scores.items():
                console.print(f"{team_name}: {score} pontos")
                team_scores[team_name] += score
            
            max_score = max(round_scores.values())
            winners = [t for t, s in round_scores.items() if s == max_score]
            if save_results:
                for team_name, p1, p2 in teams:
                    wins = 1 if team_name in winners and len(winners) == 1 else 0
                    score_p1 = round_scores[team_name] // 2
                    score_p2 = round_scores[team_name] // 2
                    save_multiplayer_score(p1, team_name, wins, score_p1, is_tournament=1)
                    save_multiplayer_score(p2, team_name, wins, score_p2, is_tournament=1)
        
        console.print(f"\n[bold green]🏁 Resultado Final do Torneio:[/bold green]")
        for team_name, total_score in team_scores.items():
            console.print(f"{team_name}: {total_score} pontos")
        
        max_total_score = max(team_scores.values())
        winners = [t for t, s in team_scores.items() if s == max_total_score]
        if len(winners) == 1:
            console.print(f"[green]🎉 {winners[0]} é a equipe campeã![/green]")
        else:
            console.print(f"[yellow]⚖️ Empate entre {', '.join(winners)}![/yellow]")
        
        if save_results and Prompt.ask("[bold cyan]Deseja revanche? (s/n)[/bold cyan]", choices=["s", "n"], default="n") == "s":
            console.print("[bold magenta]⚔️ Preparando revanche! A batalha continua! ⚔️[/bold magenta]")
            play_tournament_2x2_cli(save_results, rematch=True, prev_teams=teams, prev_max_number=max_number, prev_rounds=rounds)

def play_online_cli(mode_choice):
    player, _ = validate_unique_name(Prompt.ask("Digite seu nome, desafiante global"), [], is_team=False)
    session_id = Prompt.ask("[bold cyan]Digite o ID da sessão online[/bold cyan]")
    mode = {"1": "1x1", "2": "2x2", "3": "1x1", "4": "2x2"}[mode_choice]
    tournament = mode_choice in ["3", "4"]
    team = None
    if mode == "2x2":
        team, _ = validate_unique_name(Prompt.ask("Digite o nome da sua equipe"), [], is_team=True)
    
    max_number = get_difficulty(Prompt.ask("[bold cyan]Escolha a dificuldade (1: Fácil, 2: Médio, 3: Difícil)[/bold cyan]", choices=["1", "2", "3"], default="2"))
    rounds, _ = get_rounds(Prompt.ask("[bold cyan]Digite o número de rodadas (1-5)[/bold cyan]", default="3"))
    
    console.print(f"[bold blue]🌐 Conectando à Arena Global... Boa sorte, {player}! 🌐[/bold blue]")
    run_client(player, session_id, mode, team, max_number, rounds, tournament)

def main_cli():
    while True:
        choice = menu()
        
        if choice == "1":
            console.print("[bold green]🎮 Iniciando Singleplayer... Prepare-se para o desafio![/bold green]")
            play_singleplayer_cli()
        elif choice == "2":
            console.print("[bold green]⚔️ Iniciando Multiplayer 1x1... Que comece o duelo![/bold green]")
            play_multiplayer_1x1_cli()
        elif choice == "3":
            console.print("[bold green]🤝 Iniciando Multiplayer 2x2... A força da equipe![/bold green]")
            play_multiplayer_2x2_cli()
        elif choice == "4":
            console.print("[bold green]🏅 Iniciando Torneio 2x2... A glória espera![/bold green]")
            play_tournament_2x2_cli()
        elif choice == "5":
            console.print("[bold green]🏆 Iniciando Torneio 1x1... Prove quem é o melhor![/bold green]")
            play_tournament_1x1_cli()
        elif choice == "6":
            train_choice = show_train_menu()
            if train_choice == "1":
                console.print("[bold green]💪 Treino Singleplayer... Afie suas habilidades![/bold green]")
                play_singleplayer_cli(save_results=False)
            elif train_choice == "2":
                console.print("[bold green]💪 Treino Multiplayer 1x1... Teste seus reflexos![/bold green]")
                play_multiplayer_1x1_cli(save_results=False)
            elif train_choice == "3":
                console.print("[bold green]💪 Treino Multiplayer 2x2... Fortaleça sua equipe![/bold green]")
                play_multiplayer_2x2_cli(save_results=False)
        elif choice == "7":
            console.print("[bold green]📡 Gerenciando Rede Wi-Fi...[/bold green]")
            simulate_wifi_players_cli(max_players=4, is_team=True)
        elif choice == "8":
            rank_choice = show_rank_menu()
            if rank_choice == "1":
                console.print("[bold yellow]🏆 Exibindo Ranking Global...[/bold yellow]")
                display_ranking()
            elif rank_choice == "2":
                console.print("[bold yellow]🌞 Exibindo Ranking do Dia...[/bold yellow]")
                display_ranking(filter_type="day")
            elif rank_choice == "3":
                console.print("[bold yellow]📅 Exibindo Ranking da Semana...[/bold yellow]")
                display_ranking(filter_type="week")
            elif rank_choice == "4":
                player = Prompt.ask("[bold cyan]Digite seu nome para ver seu ranking[/bold cyan]")
                console.print("[bold yellow]👤 Exibindo Seu Ranking...[/bold yellow]")
                display_ranking(filter_type="player", player=player)
            elif rank_choice == "5":
                console.print("[bold yellow]⚔️ Exibindo Ranking Multiplayer 1x1...[/bold yellow]")
                display_multiplayer_ranking(mode="1x1")
            elif rank_choice == "6":
                console.print("[bold yellow]🤝 Exibindo Ranking Multiplayer 2x2...[/bold yellow]")
                display_multiplayer_ranking(mode="2x2")
            elif rank_choice == "7":
                console.print("[bold yellow]🏆 Exibindo Ranking Torneio 1x1...[/bold yellow]")
                display_multiplayer_ranking(mode="1x1", tournament_only=True)
            elif rank_choice == "8":
                console.print("[bold yellow]🏅 Exibindo Ranking Torneio 2x2...[/bold yellow]")
                display_multiplayer_ranking(mode="2x2", tournament_only=True)
            elif rank_choice == "9":
                console.print("[bold yellow]📜 Exibindo Histórico de Partidas...[/bold yellow]")
                display_match_history()
        elif choice == "9":
            online_choice = show_online_menu()
            if online_choice in ["1", "2", "3", "4"]:
                console.print("[bold green]🌐 Entrando na Arena Online... Prepare-se![/bold green]")
                play_online_cli(online_choice)
        elif choice == "10":
            console.print("[bold magenta]🚪 Até a próxima aventura na Arena dos Números! 🎮[/bold magenta]")
            break
        
        Prompt.ask("[bold cyan]Pressione Enter para voltar ao menu...[/bold cyan]")
