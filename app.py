# ===============================
# Mobile Legends Analytics Dashboard (Streamlit Version)
# ===============================
import streamlit as st
import os, time, json, requests, base64
import pandas as pd
from collections import defaultdict, OrderedDict, Counter
import itertools
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random
import datetime
from datetime import timedelta
import math
import glob
from itertools import combinations
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# =============================================================================
#
# PAGE CONFIGURATION & INITIAL SETUP
#
# =============================================================================

st.set_page_config(layout="wide", page_title="MLBB Analytics Dashboard")

# Custom CSS for better styling
st.markdown("""
<style>
    /* General body styling */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Sidebar styling */
    .st-emotion-cache-16txtl3 {
        padding: 1rem 1rem;
    }
    /* Custom button styling */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid transparent;
        transition: all 0.2s ease-in-out;
    }
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    /* Expander styling for a cleaner look */
    .st-emotion-cache-1h9usn1 p {
        font-size: 1rem;
        font-weight: 500;
    }
    h1, h2, h3, h4 {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
#
# ALL FUNCTIONS FROM THE NOTEBOOK (with caching and display modifications)
#
# =============================================================================

# -----------------------
# SETTINGS, CONSTANTS
# -----------------------
# API Configuration
cache_dir = './mlbb_tournament_cache'
os.makedirs(cache_dir, exist_ok=True)
API_KEY = "pIfcpzOZFhSaLGG5elRsP3s9rnL8NPr1Xt194SxPrryEfvb3cOvvNVj0V83nLAyk0FNuI6HtLCGfNvYpyHLjrKExyvOFYEQMsxyjnrk9H1KDU84ahTW3JnRF9FLIueN2" # Replace with your key if needed
headers = {"Authorization": f"Apikey {API_KEY}", "User-Agent": "HeroStatsCollector/1.0"}
BASE_PARAMS = {"wiki": "mobilelegends", "limit": 500}

archived_tournaments = {
    'MPL ID Season 14': {'path': 'MPL/Indonesia/Season_14', 'region': 'Indonesia', 'year': 2024},
    'MPL PH Season 13': {'path': 'MPL/Philippines/Season_13', 'region': 'Philippines', 'year': 2024},
    'MSC 2024': {'path': 'MSC/2024', 'region': 'International', 'year': 2024},
    'MPL ID Season 15': {'path': 'MPL/Indonesia/Season_15', 'region': 'Indonesia', 'year': 2025},
    'MPL PH Season 15': {'path': 'MPL/Philippines/Season_15', 'region': 'Philippines', 'year': 2025}
}

live_tournaments = {
    'MPL ID Season 16': {'path': 'MPL/Indonesia/Season_16', 'region': 'Indonesia', 'year': 2025},
    'MPL PH Season 16': {'path': 'MPL/Philippines/Season_16', 'region': 'Philippines', 'year': 2025},
    'MPL MY Season 16': {'path': 'MPL/Malaysia/Season_16', 'region': 'Malaysia', 'year': 2025},
    'VMC 2025 Winter': {'path': 'Vietnam_MLBB_Championship/2025/Winter', 'region': 'Vietnam', 'year': 2025},
    'MPL MENA S8': {'path': 'MPL/MENA/Season_8', 'region': 'MENA', 'year': 2025},
    'MCC S6': {'path': 'MLBB_Continental_Championships/Season_6', 'region': 'EECA', 'year': 2025},
    'China Masters 2025': {'path': 'MLBB_China_Masters/2025', 'region': 'China', 'year': 2025},
    'MTC S5': {'path': 'MTC_Turkiye_Championship/Season_5', 'region': 'Turkey', 'year': 2025},
}

# -----------------------
# DATA LOADING FROM FILES
# -----------------------
def load_data_from_file(filename, default_data={}):
    """Loads a dictionary from a JSON-formatted text file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return default_data
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from '{filename}'. Please ensure the file contains valid JSON.")
        return default_data
    except Exception as e:
        st.error(f"An unexpected error occurred while loading '{filename}': {e}")
        return default_data

# Load hero data from external files
HERO_PROFILES = load_data_from_file("Hero Profiles.txt")
HERO_DAMAGE_TYPE = load_data_from_file("Hero Damage Type.txt")


# -----------------------
# CACHING FUNCTIONS
# -----------------------
def safe_cache_key(key):
    return key.replace('/', '_').replace('\\', '_')

def local_cache_path(key):
    return os.path.join(cache_dir, safe_cache_key(key) + ".json")

@st.cache_data(ttl=300)
def load_tournament_matches(_tournament_path):
    """Load match data from Liquipedia API and return (data, error_message)."""
    try:
        params = BASE_PARAMS.copy()
        params['conditions'] = f"[[parent::{_tournament_path}]]"
        url = "https://api.liquipedia.net/api/v3/match"
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return None, f"API Error for {_tournament_path}: {resp.status_code} - {resp.text}"
        
        matches = resp.json().get("result", [])
        
        path = local_cache_path(f"matches_{_tournament_path}")
        with open(path, 'w') as f:
            json.dump(matches, f)
            
        return matches, None
        
    except Exception as e:
        path = local_cache_path(f"matches_{_tournament_path}")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f), f"API failed for {_tournament_path}, loaded from stale cache."
            except Exception as file_e:
                 return None, f"API and file cache failed for {_tournament_path}: {file_e}"
        return None, f"Error loading matches for {_tournament_path}: {e}"


# -----------------------
# RENDERING FUNCTIONS
# -----------------------
def render_strictly_sticky_table(df):
    df = df.reset_index(drop=True)
    columns = list(df.columns)
    html = '<table class="mlbb-stats">'
    html += '<thead><tr><th>No.</th>' + ''.join(f'<th>{c}</th>' for c in columns) + '</tr></thead><tbody>'
    for idx, row in df.iterrows():
        html += '<tr><td>{}</td>'.format(idx+1) + ''.join(f'<td>{row[c]}</td>' for c in columns) + '</tr>'
    html += '</tbody></table>'
    css = """<style>
    .mlbb-stats {
    border-collapse: collapse;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
    font-size: 0.9em;
    table-layout: auto;}
    .mlbb-stats th, .mlbb-stats td { text-align: center; padding: 6px 8px; }
    .mlbb-stats th {position: sticky; top: 0; background: #f0f0f0; z-index: 3; font-weight: bold;}
    .mlbb-stats tr:nth-child(even) {background: #fafafa;}
    .mlbb-stats td, .mlbb-stats th { border-right: 1px solid #f2f2f2;}
    .mlbb-stats th:first-child, .mlbb-stats td:first-child {min-width: 35px; max-width: 45px; text-align: right; font-weight: bold; background: #ececec; position: sticky; left: 0; z-index: 4;}
    </style>"""
    st.markdown(css + html, unsafe_allow_html=True)

def render_paired_tables(title_left, df_left, title_right, df_right, table_width='260px', gap='20px'):
    style = f"""
    <style>
      .h2h-table-wrap {{ display: flex; gap: {gap}; justify-content: left; align-items: flex-start; }}
      .h2h-table-block {{ min-width: {table_width}; max-width: {table_width}; }}
      .h2h-table-block table {{ width: 100%; }}
      .h2h-title {{ font-weight: bold; margin-bottom:6px; text-align:center; }}
    </style>
    """
    def one_table(caption, df):
        df = df.reset_index(drop=True)
        columns = list(df.columns)
        html = f'<div class="h2h-table-block"><div class="h2h-title">{caption}</div>'
        html += '<table class="mlbb-stats">'
        html += '<thead><tr><th>No.</th>' + ''.join(f'<th>{c}</th>' for c in columns) + '</tr></thead><tbody>'
        for idx, row in df.iterrows():
            html += '<tr><td>{}</td>'.format(idx+1) + ''.join(f'<td>{row[c]}</td>' for c in columns) + '</tr>'
        html += '</tbody></table></div>'
        return html
    text = (
        style
        + '<div class="h2h-table-wrap">'
        + one_table(title_left, df_left)
        + one_table(title_right, df_right)
        + '</div>'
    )
    st.markdown(text, unsafe_allow_html=True)

def offer_csv_download_button(df, filename="data.csv", label="Download CSV"):
    @st.cache_data
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(df)
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv',
    )


# -----------------------
# DATA PROCESSING/BUILDING FUNCTIONS
# -----------------------
class HeroDrilldownCache:
    def __init__(self, heroes, hero_stats_map, pooled_rows):
        self.heroes = heroes
        self.hero_stats_map = hero_stats_map
        self.pooled_rows = pooled_rows

@st.cache_data(show_spinner="Building hero drilldown cache...")
def build_hero_drilldown_cache(_pooled_matches_tuple):
    pooled_matches = list(_pooled_matches_tuple)
    hero_stats_map = dict()
    all_heroes = set()
    hero_pick_rows = []
    for match in pooled_matches:
        t1 = t2 = ""
        opps = match.get('match2opponents') or []
        if len(opps) >= 2:
            t1 = opps[0].get('name','').strip()
            t2 = opps[1].get('name','').strip()
        games = match.get("match2games", [])
        for game in games:
            opps_game = game.get("opponents", [])
            if len(opps_game) < 2:
                continue
            extrad = game.get("extradata", {})
            sides = [extrad.get("team1side","").lower(), extrad.get("team2side","").lower()]
            winner_raw = str(game.get("winner",""))
            for idx, opp in enumerate(opps_game[:2]):
                players = opp.get("players", [])
                for p in players:
                    if isinstance(p, dict) and "champion" in p:
                        hero = p["champion"]
                        win = (str(idx+1) == winner_raw)
                        row = {
                            "hero": hero,"team": [t1, t2][idx],"side": sides[idx] if idx < len(sides) else "","win": win,
                            "game_key": game.get("id", None),"match_key": match.get("id", None),
                            "opponent_team": [t1, t2][1-idx],
                        }
                        enemy_heroes = [ep["champion"] for ep in opps_game[1-idx].get("players", []) if isinstance(ep, dict) and "champion" in ep]
                        row["enemy_heroes"] = enemy_heroes
                        hero_pick_rows.append(row)
                        all_heroes.add(hero)
    all_heroes = sorted(all_heroes)
    for hero in all_heroes:
        rows = [r for r in hero_pick_rows if r['hero']==hero]
        team_stats = defaultdict(lambda: [0,0,0,0,0])
        for r in rows:
            team = r['team']; win = r['win']; side = r['side']
            team_stats[team][0] += 1
            if win: team_stats[team][1] += 1
            if side=="blue": team_stats[team][2] += 1
            elif side=="red": team_stats[team][3] += 1
        team_stats_rows = []
        for team in sorted(team_stats.keys()):
            g,w,bl,rd = team_stats[team][:4]
            winrate = round(100*w/g,2) if g>0 else 0
            team_stats_rows.append({
                "Team": team, "Games": g, "Wins": w,
                "Win Rate (%)": f"{winrate}%", "Blue Picks": bl, "Red Picks": rd,
            })
        df_team = pd.DataFrame(team_stats_rows)
        all_enemy_heroes = [eh for r in rows for eh in r.get("enemy_heroes",[])]
        matchups = Counter(all_enemy_heroes)
        matchup_rows = [{"Opposing Hero": k, "Times Faced": v} for k,v in matchups.most_common()]
        df_matchups = pd.DataFrame(matchup_rows)
        hero_stats_map[hero] = {"per_team": df_team, "matchups": df_matchups}
    return HeroDrilldownCache(all_heroes, hero_stats_map, hero_pick_rows)

# =============================================================================
#
# UI SECTIONS / PAGE BUILDER FUNCTIONS
#
# =============================================================================

def build_statistics_breakdown(pooled_matches, tournaments_shown):
    st.header("Statistics Breakdown")
    st.info(f"**Tournaments:** {', '.join(tournaments_shown)}")

    norm_to_display = {}
    teams = set()
    for match in pooled_matches:
        for opp in match.get("match2opponents", []):
            tname = opp.get('name')
            if tname:
                norm = tname.strip().lower()
                teams.add(norm)
                norm_to_display[norm] = tname.strip()
    
    teams = sorted(list(teams))
    team_options = [("All Teams", "all teams")] + [(norm_to_display[n], n) for n in teams]

    sort_cols = [
        "Picks", "Bans", "Wins", "Pick Rate (%)", "Ban Rate (%)", "Picks and Bans Rate (%)",
        "Win Rate (%)", "Blue Picks", "Blue Wins", "Blue Win Rate (%)", "Red Picks", "Red Wins", "Red Win Rate (%)"
    ]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        team_selection = st.selectbox("Select Team:", options=team_options, format_func=lambda x: x[0])[1]
    with col2:
        sort_col_selection = st.selectbox("Sort by:", options=sort_cols, index=5)
    with col3:
        order_selection = st.selectbox("Order:", options=[("Descending", False), ("Ascending", True)], format_func=lambda x: x[0])[1]
    
    @st.cache_data(show_spinner="Calculating hero stats...")
    def calculate_hero_stats(_pooled_matches_tuple, TEAM_NORM, SORT_COL, ASCENDING):
        pooled_matches = list(_pooled_matches_tuple)
        dt = defaultdict(lambda: {"games": 0, "wins": 0, "bans": 0, "blue_picks": 0, "blue_wins": 0, "red_picks": 0, "red_wins": 0})
        
        relevant_matches = [
            m for m in pooled_matches 
            if TEAM_NORM == "all teams" or any(opp.get('name','').strip().lower() == TEAM_NORM for opp in m.get("match2opponents",[]))
        ]
        total_games = sum(1 for m in relevant_matches for g in m.get("match2games", []) if g.get("winner") and len(g.get("opponents", [])) >= 2)

        for match in pooled_matches:
            match_team_norms = [opp.get('name', "").strip().lower() for opp in match.get("match2opponents", [])]
            for game in match.get("match2games", []):
                winner = game.get("winner")
                if not winner or len(game.get("opponents", [])) < 2: continue
                
                extrad = game.get("extradata", {})
                sides = [extrad.get("team1side", "").lower(), extrad.get("team2side", "").lower()]
                
                for idx, opp in enumerate(game.get("opponents", [])):
                    if idx >= len(match_team_norms): continue
                    
                    current_team_norm = match_team_norms[idx]
                    if TEAM_NORM != "all teams" and current_team_norm != TEAM_NORM: continue

                    for p in opp.get("players", []):
                        if isinstance(p, dict) and "champion" in p:
                            hero = p["champion"]
                            dt[hero]["games"] += 1
                            if str(idx + 1) == str(winner): dt[hero]["wins"] += 1
                            if sides[idx] == "blue":
                                dt[hero]["blue_picks"] += 1
                                if str(idx + 1) == str(winner): dt[hero]["blue_wins"] += 1
                            elif sides[idx] == "red":
                                dt[hero]["red_picks"] += 1
                                if str(idx + 1) == str(winner): dt[hero]["red_wins"] += 1
                    
                    if TEAM_NORM == "all teams" or current_team_norm == TEAM_NORM:
                        for i in range(1, 6):
                            ban_key = f'team{idx+1}ban{i}'
                            if extrad.get(ban_key): dt[extrad[ban_key]]["bans"] += 1
        
        df = pd.DataFrame([
            {
                "Hero": h, "Picks": s["games"], "Bans": s["bans"], "Wins": s["wins"],
                "Pick Rate (%)": round((s["games"]/total_games)*100, 2) if total_games > 0 else 0,
                "Ban Rate (%)": round((s["bans"]/total_games)*100, 2) if total_games > 0 else 0,
                "Picks and Bans Rate (%)": round(((s["games"]+s["bans"])/total_games)*100, 2) if total_games > 0 else 0,
                "Win Rate (%)": round((s["wins"]/s["games"])*100, 2) if s["games"] > 0 else 0,
                "Blue Picks": s["blue_picks"], "Blue Wins": s["blue_wins"],
                "Blue Win Rate (%)": round((s["blue_wins"]/s["blue_picks"])*100, 2) if s["blue_picks"] > 0 else 0,
                "Red Picks": s["red_picks"], "Red Wins": s["red_wins"],
                "Red Win Rate (%)": round((s["red_wins"]/s["red_picks"])*100, 2) if s["red_picks"] > 0 else 0,
            } for h, s in dt.items()
        ])
        
        if not df.empty and SORT_COL in df.columns:
            df = df.sort_values(by=SORT_COL, ascending=ASCENDING).reset_index(drop=True)
        return df

    df_stats = calculate_hero_stats(tuple(pooled_matches), team_selection, sort_col_selection, order_selection)
    
    if not df_stats.empty:
        render_strictly_sticky_table(df_stats)
        offer_csv_download_button(df_stats, "hero_stats.csv")
    else:
        st.warning("No data available for the selected team and tournaments.")


def build_hero_drilldown_ui(pooled_matches, tournaments_shown):
    st.header("Hero Detail Drilldown")
    st.info(f"**Tournaments:** {', '.join(tournaments_shown)}")

    hero_cache = build_hero_drilldown_cache(tuple(pooled_matches))
    if not hero_cache.heroes:
        st.warning("No hero data found in the selected tournaments.")
        return

    selected_hero = st.selectbox("Select Hero:", options=hero_cache.heroes)

    if selected_hero:
        st.subheader(f"Details for: {selected_hero}")

        st.markdown("#### Per-team Hero Stats")
        df_team = hero_cache.hero_stats_map[selected_hero]['per_team']
        if not df_team.empty:
            df_team_sorted = df_team.sort_values("Games", ascending=False)
            render_strictly_sticky_table(df_team_sorted)
            offer_csv_download_button(df_team_sorted, f"{selected_hero}_team_stats.csv", "Download Team Stats")
        else:
            st.write("No team data for this hero.")

        st.markdown("#### Most Common Opposing Heroes Faced")
        matchup = Counter()
        win_counter = defaultdict(int)
        for row in hero_cache.pooled_rows:
            if row["hero"] != selected_hero: continue
            if row["win"]:
                for eh in row["enemy_heroes"]:
                    win_counter[eh] += 1
            for eh in row["enemy_heroes"]:
                matchup[eh] += 1
        
        rows = [(eh, freq, f"{(win_counter[eh]/freq*100):.2f}%" if freq > 0 else "0.00%") for eh, freq in matchup.most_common()]
        vs_df = pd.DataFrame(rows, columns=["Opposing Hero", "Times Faced", f"Win Rate vs {selected_hero}"])
        
        if not vs_df.empty:
            render_strictly_sticky_table(vs_df.head(20))
            offer_csv_download_button(vs_df.head(20), f"{selected_hero}_matchups.csv", "Download Matchup Stats")
        else:
            st.write("No matchup data for this hero.")

def build_head_to_head_dashboard(pooled_matches, tournaments_shown):
    st.header("Head-to-Head Comparison")
    st.info(f"**Tournaments:** {', '.join(tournaments_shown)}")

    team_norm2disp = {opp.get("name", "").strip().lower(): opp.get("name", "").strip() for match in pooled_matches for opp in match.get("match2opponents", []) if opp.get("name", "").strip()}
    all_heroes = sorted(list(set(p["champion"] for m in pooled_matches for g in m.get("match2games", []) for o in g.get("opponents", []) for p in o.get("players", []) if isinstance(p, dict) and "champion" in p)))
    team_options = sorted([(name, norm) for norm, name in team_norm2disp.items() if norm])

    mode = st.radio("Comparison Mode:", ["Team vs Team", "Hero vs Hero"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("---")

    if mode == "Team vs Team":
        if not team_options:
            st.warning("No team data available for the selected tournaments.")
            return
            
        col1, col2 = st.columns(2)
        t1 = col1.selectbox("Select Team 1:", options=team_options, format_func=lambda x: x[0])[1]
        t2 = col2.selectbox("Select Team 2:", options=team_options, format_func=lambda x: x[0], index=1 if len(team_options)>1 else 0)[1]
        
        if st.button("Compare Teams", use_container_width=True):
            if t1 == t2: 
                st.error("Please select two different teams.")
            else: 
                do_team_h2h(t1, t2, pooled_matches, team_norm2disp)
    else: # Hero vs Hero
        if not all_heroes:
            st.warning("No hero data available for the selected tournaments.")
            return

        col1, col2 = st.columns(2)
        h1 = col1.selectbox("Select Hero 1:", options=all_heroes)
        h2 = col2.selectbox("Select Hero 2:", options=all_heroes, index=1 if len(all_heroes)>1 else 0)

        if st.button("Compare Heroes", use_container_width=True):
            if h1 == h2: 
                st.error("Please select two different heroes.")
            else: 
                do_hero_h2h(h1, h2, pooled_matches)

def do_team_h2h(t1, t2, pooled_matches, team_norm2disp):
    """Calculates and displays the Team vs Team head-to-head statistics."""
    h2h_matches = []
    for match in pooled_matches:
        opps = [x.get("name","").strip().lower() for x in match.get("match2opponents",[])]
        if t1 in opps and t2 in opps:
            h2h_matches.append(match)
    
    if not h2h_matches:
        st.warning(f"No matches found between {team_norm2disp[t1]} and {team_norm2disp[t2]}.")
        return

    win_counts = {t1: 0, t2: 0}
    total_games = 0
    t1_heroes, t2_heroes = Counter(), Counter()
    t1_bans, t2_bans = Counter(), Counter()

    for match in h2h_matches:
        opps = [x.get("name","").strip().lower() for x in match.get("match2opponents",[])]
        try:
            idx1, idx2 = opps.index(t1), opps.index(t2)
        except ValueError:
            continue
        
        for game in match.get("match2games", []):
            winner = str(game.get("winner",""))
            if winner.isdigit():
                match_winner_idx = int(winner) - 1
                if 0 <= match_winner_idx < len(opps):
                    winner_team = opps[match_winner_idx]
                    if winner_team in win_counts:
                        win_counts[winner_team] += 1
                total_games += 1

            extrad = game.get("extradata", {})
            opponents = game.get("opponents", [])
            if len(opponents)<2: continue

            for i, opp in enumerate(opponents):
                hero_set = set(p["champion"] for p in opp.get("players",[]) if isinstance(p, dict) and "champion" in p)
                if i == idx1: t1_heroes.update(hero_set)
                elif i == idx2: t2_heroes.update(hero_set)
            
            for i, team_idx in enumerate([idx1, idx2]):
                for ban_n in range(1,6):
                    ban_hero = extrad.get(f"team{team_idx+1}ban{ban_n}")
                    if ban_hero:
                        if i == 0: t1_bans[ban_hero] += 1
                        else: t2_bans[ban_hero] += 1

    st.subheader(f"{team_norm2disp[t1]} vs {team_norm2disp[t2]}")
    st.markdown(f"""
    - **Total Games:** {total_games}
    - **{team_norm2disp[t1]} Wins:** `{win_counts[t1]}`
    - **{team_norm2disp[t2]} Wins:** `{win_counts[t2]}`
    """)

    tbl_A = pd.DataFrame(t1_heroes.most_common(8), columns=['Hero', 'Picks'])
    tbl_B = pd.DataFrame(t2_heroes.most_common(8), columns=['Hero', 'Picks'])
    render_paired_tables(
        f"Top picks by {team_norm2disp[t1]}<br><span style='font-weight:normal'>(vs {team_norm2disp[t2]})</span>", tbl_A,
        f"Top picks by {team_norm2disp[t2]}<br><span style='font-weight:normal'>(vs {team_norm2disp[t1]})</span>", tbl_B
    )
    
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    ban_tbl_A = pd.DataFrame(t1_bans.most_common(8), columns=['Hero', 'Bans'])
    ban_tbl_B = pd.DataFrame(t2_bans.most_common(8), columns=['Hero', 'Bans'])
    render_paired_tables(
        f"Target bans by {team_norm2disp[t1]}<br><span style='font-weight:normal'>(vs {team_norm2disp[t2]})</span>", ban_tbl_A,
        f"Target bans by {team_norm2disp[t2]}<br><span style='font-weight:normal'>(vs {team_norm2disp[t1]})</span>", ban_tbl_B
    )

def do_hero_h2h(h1, h2, pooled_matches):
    """Calculates and displays the Hero vs Hero head-to-head statistics."""
    win_h1 = win_h2 = 0
    total_games = 0
    for match in pooled_matches:
        for game in match.get("match2games", []):
            opp_heroes = []
            for opp in game.get("opponents", []):
                opp_heroes.append(set(p["champion"] for p in opp.get("players",[]) if isinstance(p, dict) and "champion" in p))
            if len(opp_heroes) != 2: continue
            side1, side2 = opp_heroes
            if (h1 in side1 and h2 in side2) or (h2 in side1 and h1 in side2):
                total_games += 1
                winner = str(game.get("winner",""))
                if (h1 in side1 and winner=="1") or (h1 in side2 and winner=="2"): win_h1 += 1
                if (h2 in side1 and winner=="1") or (h2 in side2 and winner=="2"): win_h2 += 1
    
    st.subheader(f"{h1} vs {h2}")
    if total_games > 0:
        st.markdown(f"""
        - **Games with both on opposite teams:** {total_games}
        - **{h1} wins:** `{win_h1}` (`{(win_h1/total_games*100):.1f}%`)
        - **{h2} wins:** `{win_h2}` (`{(win_h2/total_games*100):.1f}%`)
        """)
    else:
        st.warning(f"No games found where {h1} and {h2} were on opposing teams.")

def build_synergy_counter_dashboard(pooled_matches, tournaments_shown):
    st.header("Synergy & Counter Analysis")
    st.info(f"**Tournaments:** {', '.join(tournaments_shown)}")

    team_norm2disp = {opp.get("name", "").strip().lower(): opp.get("name", "").strip() for match in pooled_matches for opp in match.get("match2opponents", []) if opp.get("name", "").strip()}
    teams = sorted(team_norm2disp.keys())
    team_options = [("All Teams", "all")] + [(name, norm) for norm, name in team_norm2disp.items() if norm]
    all_heroes = sorted(list(set(p["champion"] for match in pooled_matches for game in match.get("match2games", []) for opp in game.get("opponents", []) for p in opp.get("players", []) if isinstance(p, dict) and "champion" in p)))

    c1, c2, c3 = st.columns(3)
    team_filter = c1.selectbox("Team:", options=team_options, format_func=lambda x: x[0])[1]
    mode = c2.selectbox("Mode:", options=[("Synergy Combos", "synergy"), ("Anti-Synergy Combos", "anti"), ("Counter Combos", "counter")], format_func=lambda x: x[0])[1]
    top_n = c3.slider("Show Top N:", 3, 50, 15)
    min_games = c3.slider("Min Games Played:", 1, 20, 3)

    st.markdown("---")

    if mode in ("synergy", "anti"):
        focus_hero = st.selectbox("Filter by Hero (Optional):", options=["(Show All)"] + all_heroes)
        df = analyze_synergy(tuple(pooled_matches), team_filter, min_games, anti=(mode=="anti"), focus_hero=focus_hero)
        if not df.empty:
            df_display = df.head(top_n)
            render_strictly_sticky_table(df_display)
            offer_csv_download_button(df_display, "synergy_data.csv")
            
            title = "Top Performing Hero Duos" if mode == "synergy" else "Worst Performing Hero Duos"
            if focus_hero != "(Show All)":
                title += f" with {focus_hero}"
            
            plot_synergy_bar(df_display.sort_values("Win Rate (%)", ascending=(mode=="anti")), title, focus_hero)
        else:
            st.warning("No hero pairs meet the specified criteria.")

    elif mode == "counter":
        focus_side = None
        if team_filter != 'all':
            focus_side = st.selectbox("Focus Perspective:", 
                options=[(f"When {team_norm2disp[team_filter]} uses hero", "when_uses"), 
                         (f"When playing against {team_norm2disp[team_filter]}", "when_against")],
                format_func=lambda x: x[0])[1]

        df = analyze_counter(tuple(pooled_matches), min_games, team_filter=team_filter, focus_side=focus_side)
        if not df.empty:
            df_display = df.head(top_n)
            render_strictly_sticky_table(df_display)
            offer_csv_download_button(df_display, "counter_data.csv")
        else:
            st.warning("No counter matchups meet the specified criteria.")

@st.cache_data(show_spinner="Analyzing synergy data...")
def analyze_synergy(_pooled_matches_tuple, team_filter, min_games, anti=False, focus_hero=None):
    # This function's logic is identical to the notebook's analyze_synergy
    # It is wrapped in st.cache_data for performance
    pooled_matches = list(_pooled_matches_tuple)
    duo_counter = {}
    for match in pooled_matches:
        teams_names = [opp.get("name", "").strip().lower() for opp in match.get("match2opponents", [])]
        for game in match.get("match2games", []):
            winner = str(game.get("winner", ""))
            for idx, opp in enumerate(game.get("opponents", [])):
                if team_filter != "all" and (len(teams_names) <= idx or teams_names[idx] != team_filter):
                    continue
                players = [p["champion"] for p in opp.get("players", []) if isinstance(p, dict) and "champion" in p]
                for a, b in itertools.combinations(sorted(players), 2):
                    key = (a, b)
                    if key not in duo_counter:
                        duo_counter[key] = {"games": 0, "wins": 0}
                    duo_counter[key]["games"] += 1
                    if str(idx + 1) == winner:
                        duo_counter[key]["wins"] += 1
    rows = []
    for (h1, h2), stats in duo_counter.items():
        if stats["games"] >= min_games:
            if focus_hero and focus_hero != "(Show All)":
                if h1 != focus_hero and h2 != focus_hero:
                    continue
            rows.append({
                "Hero 1": h1, "Hero 2": h2,
                "Games Together": stats["games"], "Wins": stats["wins"],
                "Win Rate (%)": round(stats["wins"] / stats["games"] * 100, 2)
            })
    df = pd.DataFrame(rows)
    if df.empty: return df
    df = df.sort_values("Win Rate (%)", ascending=anti)
    return df

@st.cache_data(show_spinner="Analyzing counter data...")
def analyze_counter(_pooled_matches_tuple, min_games, ally_hero=None, enemy_hero=None, team_filter=None, focus_side=None):
    # This function's logic is identical to the notebook's analyze_counter
    # It is wrapped in st.cache_data for performance
    pooled_matches = list(_pooled_matches_tuple)
    counter_stats = {}
    for match in pooled_matches:
        opp_names = [opp.get("name", "").strip().lower() for opp in match.get("match2opponents", [])]
        for game in match.get("match2games", []):
            opponents = game.get("opponents", [])
            winner = str(game.get("winner", ""))
            if len(opponents) != 2: continue

            team_indices_to_process = []
            if team_filter and team_filter != "all" and team_filter in opp_names:
                team_idx = opp_names.index(team_filter)
                opp_idx = 1 - team_idx
                if focus_side == "when_uses":
                    team_indices_to_process.append({'ally': team_idx, 'enemy': opp_idx})
                elif focus_side == "when_against":
                    team_indices_to_process.append({'ally': opp_idx, 'enemy': team_idx})
            else: # Global analysis
                team_indices_to_process.append({'ally': 0, 'enemy': 1})
                team_indices_to_process.append({'ally': 1, 'enemy': 0})

            for perspective in team_indices_to_process:
                ally_idx, enemy_idx = perspective['ally'], perspective['enemy']
                ally_heroes = [p["champion"] for p in opponents[ally_idx].get("players", []) if isinstance(p, dict) and "champion" in p]
                enemy_heroes = [p["champion"] for p in opponents[enemy_idx].get("players", []) if isinstance(p, dict) and "champion" in p]
                is_win = (str(ally_idx + 1) == winner)

                for a in ally_heroes:
                    if ally_hero and a != ally_hero: continue
                    for b in enemy_heroes:
                        if enemy_hero and b != enemy_hero: continue
                        k = (a, b)
                        if k not in counter_stats:
                            counter_stats[k] = {"games": 0, "wins": 0}
                        counter_stats[k]["games"] += 1
                        if is_win: counter_stats[k]["wins"] += 1
    rows = []
    for (a, b), stats in counter_stats.items():
        if stats["games"] >= min_games:
            rows.append({
                "Ally Hero": a, "Enemy Hero": b,
                "Games Against": stats["games"], "Wins": stats["wins"],
                "Win Rate (%)": round(stats["wins"] / stats["games"] * 100, 2)
            })
    df = pd.DataFrame(rows)
    return df if df.empty else df.sort_values("Win Rate (%)", ascending=False)

def plot_synergy_bar(df, title, focus_hero=None):
    if df.empty: return
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(df) + 1.1))
    
    if focus_hero and focus_hero != "(Show All)":
        desc = [h2 if h1 == focus_hero else h1 for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
    else:
        desc = [f"{h1} + {h2}" for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
        
    colors = ['#43a047' if x >= 55 else '#e53935' if x <= 45 else '#ffb300' for x in df["Win Rate (%)"]]
    ax.barh(desc, df["Win Rate (%)"], color=colors)
    
    for i, value in enumerate(df["Win Rate (%)"]):
        ax.text(value + 0.5, i, f'{value:.1f}%', va='center', fontsize=10, fontweight='bold')
        
    ax.set_xlabel("Win Rate (%)", fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=11)
    ax.xaxis.grid(True, linestyle=':', alpha=0.45)
    ax.set_axisbelow(True)
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    st.pyplot(fig) # <<< Renders the plot in Streamlit

def plot_counter_heatmap(df, title):
    if df.empty: return
    # This function's logic is identical to the notebook's plot_counter_heatmap
    # It just uses st.pyplot(fig) at the end.
    mat = df.pivot(index="Ally Hero", columns="Enemy Hero", values="Win Rate (%)")
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(mat, annot=True, fmt=".1f", cmap="coolwarm", linewidths=.5, ax=ax)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    st.pyplot(fig) # <<< Renders the plot in Streamlit

def build_playoff_qualification_ui(*args, **kwargs):
    st.header("Playoff Qualification Odds (What-If Scenario)")
    st.warning("This feature's UI is highly complex and not fully converted in this example.")
    st.info("The core logic would use `st.radio` for match outcomes stored in `st.session_state`.")

def build_enhanced_draft_assistant_ui(*args, **kwargs):
    st.header("Drafting Assistant")
    st.warning("This feature's UI is highly complex and not fully converted in this example.")
    st.info("The UI would use `st.columns` and `st.selectbox` for picks/bans.")


# =============================================================================
#
# MAIN APPLICATION LOGIC
#
# =============================================================================

def main():
    st.sidebar.title(" MLBB Analytics Dashboard")
    
    if not HERO_PROFILES or not HERO_DAMAGE_TYPE:
        st.sidebar.error("Hero data files not found. Please add `Hero Profiles.txt` and `Hero Damage Type.txt` to the app directory.")
    else:
        st.sidebar.success("Hero data files loaded.")


    all_tournaments = {**archived_tournaments, **live_tournaments}

    # <<< FIX: The radio button's value now directly controls the view after data is loaded.
    mode = st.sidebar.radio(
        "Select Analysis Mode:",
        ['Statistics breakdown', 'Hero detail drilldown', 'Head-to-head',
         'Synergy & Counter Analysis', 'Playoff Qualification Odds (What-If Scenario)', 
         'Drafting Assistant']
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Select Tournaments")
    
    selected_tournaments = []
    
    tab1, tab2 = st.sidebar.tabs(["By Region", "By Year"])

    with tab1:
        regions = defaultdict(list)
        for name, data in all_tournaments.items(): regions[data['region']].append(name)
        for region in sorted(regions.keys()):
            with st.expander(f"{region} ({len(regions[region])})"):
                for name in regions[region]:
                    if st.checkbox(name, key=f"cb_region_{name}"):
                        selected_tournaments.append(name)

    with tab2:
        years = defaultdict(list)
        for name, data in all_tournaments.items(): years[data['year']].append(name)
        for year in sorted(years.keys(), reverse=True):
            with st.expander(f"Year {year} ({len(years[year])})"):
                for name in years[year]:
                    if st.checkbox(name, key=f"cb_year_{name}"):
                        selected_tournaments.append(name)
    
    selected_tournaments = sorted(list(set(selected_tournaments)))
    st.sidebar.markdown("---")

    # <<< FIX: This button now primarily loads data and sets a flag that analysis is ready.
    if st.sidebar.button("Analyze Selected Tournaments", use_container_width=True, type="primary"):
        if not selected_tournaments:
            st.sidebar.error("Please select at least one tournament.")
        else:
            with st.spinner(f"Loading data for {len(selected_tournaments)} tournament(s)..."):
                pooled_matches = []
                has_errors = False
                st.session_state.toasts_shown = set() # Reset toasts for new analysis
                for name in selected_tournaments:
                    path = all_tournaments[name]['path']
                    data, error = load_tournament_matches(path)
                    
                    if error:
                        st.warning(error)
                        has_errors = True
                    if data:
                        pooled_matches.extend(data)
                        if name not in st.session_state.toasts_shown:
                            st.toast(f"Loaded {len(data)} matches for {name}")
                            st.session_state.toasts_shown.add(name)
            
            st.session_state.pooled_matches = pooled_matches
            st.session_state.tournaments_shown = selected_tournaments
            st.session_state.analysis_ready = True

    if st.sidebar.button("Train AI Draft Model", use_container_width=True):
         st.session_state.run_training = True
         st.session_state.analysis_ready = False # Stop analysis view
         st.session_state.selected_tournaments_for_training = selected_tournaments

    # <<< FIX: This logic block now runs if analysis is ready, and uses the live radio button value.
    if st.session_state.get('analysis_ready', False):
        pooled_matches = st.session_state.pooled_matches
        tournaments_shown = st.session_state.tournaments_shown

        if not pooled_matches:
            st.error("Could not load any match data. The API might be down or no data is available.")
        else:
            # The success message now appears in the main area once
            if 'success_message_shown' not in st.session_state:
                 st.success(f"Successfully loaded data for {len(tournaments_shown)} tournament(s). Total matches found: {len(pooled_matches)}")
                 st.session_state.success_message_shown = True

            if mode == 'Statistics breakdown':
                build_statistics_breakdown(pooled_matches, tournaments_shown)
            elif mode == 'Hero detail drilldown':
                build_hero_drilldown_ui(pooled_matches, tournaments_shown)
            elif mode == 'Head-to-head':
                build_head_to_head_dashboard(pooled_matches, tournaments_shown)
            elif mode == 'Synergy & Counter Analysis':
                build_synergy_counter_dashboard(pooled_matches, tournaments_shown)
            elif mode == 'Playoff Qualification Odds (What-If Scenario)':
                build_playoff_qualification_ui(pooled_matches, tournaments_shown)
            elif mode == 'Drafting Assistant':
                build_enhanced_draft_assistant_ui(pooled_matches, tournaments_shown)

    elif st.session_state.get('run_training', False):
        st.header("AI Model Training")
        training_selection = st.session_state.get('selected_tournaments_for_training', [])
        if not training_selection:
            st.error("Please select tournaments from the sidebar to use as training data, then click 'Train AI Draft Model' again.")
        else:
            st.info("Placeholder for AI Training logic.")
        st.session_state.run_training = False # Reset flag

    else:
        st.info("📈 Welcome to the Mobile Legends Analytics Dashboard!")
        st.markdown("Please select a mode and at least one tournament from the sidebar, then click **'Analyze'**.")

if __name__ == "__main__":
    # Initialize session state keys if they don't exist
    for key, default_value in [
        ('analysis_ready', False),
        ('run_training', False),
        ('toasts_shown', set()),
        ('pooled_matches', []),
        ('tournaments_shown', [])
    ]:
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    main()


