import sqlite3
from datetime import datetime, timedelta
import json

def init_db():
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS singleplayer_scores
                 (player TEXT, attempts INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS multiplayer_scores
                 (player TEXT, team TEXT, wins INTEGER, score INTEGER, date TEXT, is_tournament INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wifi_players
                 (player TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS online_sessions
                 (player TEXT, session_id TEXT, mode TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def save_score(player, attempts):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("INSERT INTO singleplayer_scores (player, attempts, date) VALUES (?, ?, ?)",
              (player, attempts, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def save_multiplayer_score(player, team, wins, score, is_tournament=0):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("INSERT INTO multiplayer_scores (player, team, wins, score, date, is_tournament) VALUES (?, ?, ?, ?, ?, ?)",
              (player, team, wins, score, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), is_tournament))
    conn.commit()
    conn.close()

def save_wifi_player(player):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO wifi_players (player) VALUES (?)", (player,))
    conn.commit()
    conn.close()

def remove_wifi_player(player):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("DELETE FROM wifi_players WHERE player = ?", (player,))
    conn.commit()
    conn.close()

def fetch_wifi_players():
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("SELECT player FROM wifi_players")
    players = [row[0] for row in c.fetchall()]
    conn.close()
    return players

def check_player_exists(player):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM singleplayer_scores WHERE player = ? UNION SELECT 1 FROM multiplayer_scores WHERE player = ?", (player, player))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def check_team_exists(team):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM multiplayer_scores WHERE team = ?", (team,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def fetch_scores(filter_type=None, player=None):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    query = "SELECT player, attempts, date FROM singleplayer_scores"
    params = []
    if filter_type == "day":
        query += " WHERE date >= ?"
        params.append((datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
    elif filter_type == "week":
        query += " WHERE date >= ?"
        params.append((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'))
    elif filter_type == "player" and player:
        query += " WHERE player = ?"
        params.append(player)
    query += " ORDER BY attempts DESC, date DESC LIMIT 10"
    c.execute(query, params)
    scores = c.fetchall()
    conn.close()
    return scores

def fetch_multiplayer_scores(mode="1x1", tournament_only=False):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    is_tournament = 1 if tournament_only else 0
    if mode == "1x1":
        query = """SELECT player, SUM(wins), AVG(score), MAX(date)
                   FROM multiplayer_scores
                   WHERE is_tournament = ? AND team IS NULL
                   GROUP BY player
                   ORDER BY SUM(wins) DESC, AVG(score) DESC, MAX(date) DESC LIMIT 10"""
        c.execute(query, (is_tournament,))
        scores = c.fetchall()
    else:  # mode == "2x2"
        query = """SELECT team, player, SUM(wins), AVG(score), MAX(date)
                   FROM multiplayer_scores
                   WHERE is_tournament = ? AND team IS NOT NULL
                   GROUP BY team, player
                   ORDER BY SUM(wins) DESC, AVG(score) DESC, MAX(date) DESC LIMIT 10"""
        c.execute(query, (is_tournament,))
        scores = c.fetchall()
    conn.close()
    return scores

def fetch_match_history():
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("""SELECT player, team, wins, score, date, is_tournament
                 FROM multiplayer_scores
                 ORDER BY date DESC LIMIT 50""")
    history = c.fetchall()
    conn.close()
    return history

def save_online_session(player, session_id, mode):
    conn = sqlite3.connect('arena.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO online_sessions (player, session_id, mode, date) VALUES (?, ?, ?, ?)",
              (player, session_id, mode, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()