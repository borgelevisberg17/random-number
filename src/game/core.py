import random
from src.database import check_player_exists, check_team_exists

def get_badge(wins):
    if wins >= 20:
        return "🏆 Lenda Suprema"
    elif wins >= 10:
        return "⭐ Mestre dos Números"
    elif wins >= 5:
        return "🎖 Guerreiro da Arena"
    elif wins >= 1:
        return "🌟 Novato Promissor"
    return "⚪ Aspirante"

def validate_unique_name(name, existing_names, is_team=False, is_wifi=False):
    if len(name) > 20:
        return False, "O nome deve ter no máximo 20 caracteres!"
    if name in existing_names:
        return False, "Este nome já está em uso! Tente outro."
    if is_team and check_team_exists(name):
        return False, "Esta equipe já está registrada! Escolha outra."
    if not is_team and not is_wifi and check_player_exists(name):
        return False, "Este jogador já foi registrado! Escolha outro."
    return True, ""

def get_rounds(rounds_str):
    try:
        rounds = int(rounds_str)
        if 1 <= rounds <= 5:
            return True, rounds
        return False, "O número de rodadas deve estar entre 1 e 5!"
    except ValueError:
        return False, "Por favor, insira um número inteiro!"

def get_difficulty(choice):
    return {"1": 10, "2": 20, "3": 50}.get(choice, 20)

def play_singleplayer(name, max_number, save_results=True):
    secret_number = random.randint(1, max_number)
    return {"name": name, "max_number": max_number, "secret_number": secret_number, "attempts": 0, "hint_used": False, "save_results": save_results}

def play_round(player, numbers, max_number, attempts, hint_used, guess=None):
    if not guess:
        return {"status": "continue", "message": f"Número {len(attempts) + 1} (1 a {max_number}) - 3 tentativas", "score": 0}

    if guess.lower() == 'dica' and not hint_used:
        hint_used = True
        return {"status": "hint", "message": f"Dica: O número é {'par' if numbers[len(attempts)] % 2 == 0 else 'ímpar'}!", "score": 0, "hint_used": hint_used}

    try:
        guess = int(guess)
    except ValueError:
        return {"status": "error", "message": "Insira um número inteiro ou 'dica'!", "score": 0, "hint_used": hint_used}

    secret_number = numbers[len(attempts)]
    attempts.append(guess)

    if guess < secret_number:
        return {"status": "guess", "message": "Muito baixo!", "score": 0, "hint_used": hint_used}
    elif guess > secret_number:
        return {"status": "guess", "message": "Muito alto!", "score": 0, "hint_used": hint_used}
    else:
        points = max(1, 4 - len(attempts) - (1 if hint_used else 0))
        return {"status": "correct", "message": f"Acertou o número {len(attempts)}! (+{points} pontos)", "score": points, "hint_used": False}
