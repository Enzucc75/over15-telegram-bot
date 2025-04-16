
import requests
import time
from telegram import Bot

# === CONFIG ===
API_KEY = "00a52e0937d965bfd1ef1fb6e9212a30"
BOT_TOKEN = "7958415664:AAGNwx5tLUiOxvnjV0EqKRwU2n3JYyC11as"
CHAT_ID = "1047643639"
LEAGUE_IDS = [
    39, 40, 61, 62, 135, 136, 78, 79, 140, 141, 2, 3, 848, 849,
    4, 5, 94, 253, 556, 557, 764, 775, 384, 385
]

bot = Bot(token=BOT_TOKEN)
bot.send_message(chat_id=CHAT_ID, text="✅ Il bot FASE 4 è partito con successo!")

# === FUNZIONE ANALISI FORMA ===
def get_team_form(team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&season=2023"
    headers = {"x-apisports-key": API_KEY}
    res = requests.get(url, headers=headers)
    data = res.json()
    
    wins = data["response"].get("form", "").count("W")
    draws = data["response"].get("form", "").count("D")
    losses = data["response"].get("form", "").count("L")
    gf = data["response"].get("goals", {}).get("for", {}).get("total", {}).get("total", 0)
    ga = data["response"].get("goals", {}).get("against", {}).get("total", {}).get("total", 0)
    return f"{wins}V {draws}P {losses}S | {gf} GF – {ga} GS"

# === FUNZIONE PRINCIPALE ===
def check_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()

    if not data.get("response"):
        return

    for match in data["response"]:
        league_id = match["league"]["id"]
        if league_id not in LEAGUE_IDS:
            continue

        fixture_id = match["fixture"]["id"]
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        home_id = match["teams"]["home"]["id"]
        away_id = match["teams"]["away"]["id"]
        goals_home = match["goals"]["home"] or 0
        goals_away = match["goals"]["away"] or 0
        total_goals = goals_home + goals_away
        status = match["fixture"]["status"]["short"]
        minute = match["fixture"]["status"].get("elapsed", 0)

        if not (status in ("1H", "2H") and total_goals == 1 and 10 <= minute <= 85):
            continue

        # === RECUPERO QUOTE LIVE ===
        odds_url = f"https://v3.football.api-sports.io/odds/live?fixture={fixture_id}"
        odds_res = requests.get(odds_url, headers=headers)
        odds_data = odds_res.json()

        odd_value = None
        try:
            for book in odds_data["response"]:
                for bet in book.get("bets", []):
                    if bet["name"] == "Over/Under 1.5 goals":
                        for value in bet["values"]:
                            if value["value"] == "Over 1.5":
                                odd_value = float(value["odd"])
                                break
        except:
            pass

        if not odd_value or odd_value < 1.5:
            continue

        # === STATISTICHE LIVE ===
        stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
        stats_res = requests.get(stats_url, headers=headers)
        stats_data = stats_res.json()

        total_shots_on_target = 0
        dangerous_attacks = 0

        try:
            for team_stats in stats_data["response"]:
                for stat in team_stats.get("statistics", []):
                    if stat["type"] == "Shots on Goal":
                        total_shots_on_target += stat["value"] or 0
                    elif stat["type"] == "Dangerous Attacks":
                        dangerous_attacks += stat["value"] or 0
        except:
            pass

        if total_shots_on_target < 3 or dangerous_attacks < 50:
            continue

        # === FORMA SQUADRE ===
        try:
            form_home = get_team_form(home_id)
            form_away = get_team_form(away_id)
        except:
            form_home = "N/A"
            form_away = "N/A"

        message = (
            f"📊 *Match interessante per Over 1.5!*
"
            f"⚽️ {home} vs {away} – Minuto {minute}
"
            f"Risultato: {goals_home}-{goals_away}
"
            f"Quota Over 1.5: {odd_value}
"
            f"Tiri in porta: {total_shots_on_target}
"
            f"Attacchi pericolosi: {dangerous_attacks}
"
            f"📈 Forma {home}: {form_home}
"
            f"📈 Forma {away}: {form_away}"
        )
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# === LOOP ===
while True:
    try:
        check_matches()
    except Exception as e:
        print(f"❌ Errore: {e}")
    time.sleep(300)  # ogni 5 minuti
