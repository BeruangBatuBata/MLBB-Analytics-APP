# ===================================================================
# FINAL COMPLETE SCRIPT: MLBB Drafting Assistant
# ===================================================================

# --- SECTION 1: IMPORTS AND PAGE CONFIGURATION ---
import streamlit as st
import pandas as pd
import joblib
import itertools
import math
import numpy as np
from collections import defaultdict

# Page config must be the first Streamlit command
st.set_page_config(
    layout="wide",
    page_title="MLBB Pro Drafting Assistant",
    page_icon="🎯"
)

# ===================================================================
# SECTION 2: DATA DICTIONARIES AND CONSTANTS
# ===================================================================

# This dictionary provides the strategic context for each hero.
HERO_PROFILES = {
    # A
    'Aamon':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'Magic Damage', 'Conceal', 'Pick-off']}],
    'Akai':     [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Control', 'Set-up', 'Front-line', 'Forced Movement']}],
    'Aldous':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Late Game', 'Carry', 'Burst', 'Global Presence']}],
    'Alice':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Mage'], 'tags': ['Sustain', 'Dive', 'Magic Damage', 'AoE Damage']}],
    'Alpha':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Control', 'AoE Damage', 'Stun']}],
    'Alucard':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Carry', 'Early Game']}],
    'Angela':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Utility', 'Heal', 'Shield', 'Peel', 'Global Presence', 'Slow']}],
    'Argus':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Late Game', 'Immunity', 'Push']}],
    'Arlott': [
        {'build_name': 'Damage', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Dive', 'Pick-off', 'Carry', 'Stun']},
        {'build_name': 'Tank', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Sustain', 'Control', 'Front-line', 'Set-up']}
    ],
    'Atlas':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'AoE Damage', 'Front-line', 'Airborne']}],
    'Aulus':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Late Game', 'High Mobility', 'Sustain Damage']}],
    'Aurora':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Control', 'Magic Damage', 'Freeze']}],
    # B
    'Badang':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Control', 'Set-up', 'Airborne']}],
    'Balmond':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'AoE Damage']}],
    'Bane':     [{'build_name': 'Magic', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Poke', 'AoE Damage', 'Push', 'Magic Damage']}],
    'Barats':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Front-line', 'Control', 'Carry', 'AoE Damage']}],
    'Baxia':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank'], 'tags': ['Sustain', 'High Mobility', 'Anti-Heal', 'Short Dash']}],
    'Beatrix':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Poke', 'Burst', 'Sustain Damage']}],
    'Belerick': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Control', 'Front-line', 'Peel', 'Taunt']}],
    'Benedetta':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Sustain', 'Immunity', 'Split Push', 'Multi-Dash']}],
    'Brody':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Early Game', 'Burst', 'Poke']}],
    'Bruno':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Sustain Damage']}],
    # C
    'Carmilla': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Control', 'Set-up', 'Sustain', 'Slow']}],
    'Cecilion': [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Late Game', 'Poke', 'Burst', 'AoE Damage']}],
    "Chang'e":  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'High Mobility', 'Sustain Damage']}],
    'Chip':     [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Utility', 'Global Presence', 'Peel', 'Wall Pass']}],
    'Chou': [
        {'build_name': 'Damage', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Pick-off', 'High Mobility', 'Immunity', 'Airborne']},
        {'build_name': 'Utility', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Peel', 'Control', 'Initiator', 'Vision', 'Airborne']}
    ],
    'Cici':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'High Mobility', 'Poke', 'Sustain Damage']}],
    'Claude':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage', 'High Mobility', 'Multi-Dash']}],
    'Clint':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Early Game', 'Burst', 'Poke']}],
    'Cyclops':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Mage'], 'tags': ['Burst', 'Magic Damage', 'Single Target CC', 'Immobilize']}],
    # D
    'Diggie':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Utility', 'Disengage', 'Peel', 'Vision', 'Anti-CC']}],
    'Dyrroth':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Early Game', 'Dive', 'Anti-Tank']}],
    # E
    'Edith':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Marksman'], 'tags': ['Control', 'Front-line', 'Carry', 'Magic Damage', 'Airborne']}],
    'Esmeralda':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Mage', 'Tank'], 'tags': ['Sustain', 'Front-line', 'High Mobility', 'Sustain Damage']}],
    'Estes':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Sustain', 'Utility', 'Peel']}],
    'Eudora':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Magic Damage', 'Pick-off', 'Stun']}],
    # F
    'Fanny':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Split Push', 'Unlimited Dash', 'Wall Pass']}],
    'Faramis':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Support', 'Mage'], 'tags': ['Utility', 'AoE Damage', 'Magic Damage', 'Objective Control']}],
    'Floryn':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Sustain', 'Utility', 'Global Presence']}],
    'Franco':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Pick-off', 'Single Target CC', 'Control', 'Suppress']}],
    'Fredrinn': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Control', 'Front-line', 'Utility', 'Taunt']}],
    'Freya':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Burst', 'AoE Damage']}],
    # G
    'Gatotkaca':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Initiator', 'Control', 'Front-line', 'Taunt']}],
    'Gloo':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Control', 'Dive', 'Immobilize']}],
    'Gord':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Magic Damage', 'Sustain Damage']}],
    'Granger':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Marksman'], 'tags': ['Burst', 'Early Game']}],
    'Grock':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Front-line', 'Burst', 'Petrify']}],
    'Guinevere':[{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Burst', 'Set-up', 'Magic Damage', 'Airborne', 'Charm']}],
    'Gusion':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Burst', 'High Mobility', 'Magic Damage', 'Pick-off']}],
    # H
    'Hanabi':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'AoE Damage', 'Immunity']}],
    'Hanzo':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Carry', 'Late Game']}],
    'Harith':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Mage'], 'tags': ['Sustain', 'High Mobility', 'Magic Damage', 'Carry', 'Sustain Damage']}],
    'Harley':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Mage', 'Assassin'], 'tags': ['Burst', 'Pick-off', 'Magic Damage']}],
    'Hayabusa': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Pick-off', 'Split Push', 'Multi-Dash']}],
    'Helcurt':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'Pick-off', 'Map Control', 'Silence']}],
    'Hilda':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Fighter'], 'tags': ['Sustain', 'Early Game', 'High Mobility']}],
    'Hylos':    [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Front-line', 'Control', 'Stun']}],
    # I
    'Irithel':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage', 'Sustain Damage']}],
    'Ixia':     [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['AoE Damage', 'Sustain', 'Late Game', 'Sustain Damage']}],
    # J
    'Jawhead':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Pick-off', 'Single Target CC', 'Burst', 'Forced Movement']}],
    'Johnson':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Global Presence', 'Set-up', 'Burst', 'Long Dash']}],
    'Joy':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Assassin', 'Mage'], 'tags': ['High Mobility', 'Immunity', 'Dive', 'Magic Damage', 'Multi-Dash']}],
    'Julian':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Burst', 'Control', 'Sustain', 'AoE Damage']}],
    # K
    'Kadita':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Mage'], 'tags': ['Burst', 'Initiator', 'Immunity', 'Airborne']}],
    'Kagura':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Poke', 'High Mobility']}],
    'Kaja':     [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support', 'Fighter'], 'tags': ['Pick-off', 'Single Target CC', 'Control', 'Suppress']}],
    'Karina':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Burst', 'Magic Damage', 'Carry']}],
    'Karrie':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Anti-Tank']}],
    'Khaleed':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'AoE Damage']}],
    'Khufra':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Control', 'Anti-Mobility', 'Airborne']}],
    'Kimmy':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Mage'], 'tags': ['Poke', 'Late Game', 'Hybrid Damage', 'Sustain Damage']}],
    # L
    'Lancelot': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Immunity', 'Multi-Dash']}],
    'Lapu-Lapu':[{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['AoE Damage', 'Sustain', 'Dive']}],
    'Layla':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Long Range']}],
    'Leomord':  [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'High Mobility', 'Carry']}],
    'Lesley':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Burst', 'Poke']}],
    'Ling':     [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['High Mobility', 'Burst', 'Carry', 'Late Game', 'Wall Pass']}],
    'Lolita':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Peel', 'Set-up', 'Initiator', 'Front-line', 'Stun']}],
    'Lunox':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Sustain', 'Magic Damage', 'Anti-Tank']}],
    'Luo Yi':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Set-up', 'AoE Damage', 'Global Presence', 'Forced Movement']}],
    'Lylia':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Magic Damage', 'High Mobility', 'Slow']}],
    # M
    'Martis':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Carry', 'Early Game', 'Immunity', 'Airborne']}],
    'Masha':    [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Split Push', 'Sustain', 'Anti-Tank']}],
    'Mathilda': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support', 'Assassin'], 'tags': ['Utility', 'High Mobility', 'Dive', 'Peel', 'Long Dash']}],
    'Melissa':  [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'Peel']}],
    'Minotaur': [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank', 'Support'], 'tags': ['Initiator', 'Set-up', 'Heal', 'Front-line', 'Airborne']}],
    'Minsitthar':[{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Fighter', 'Support'], 'tags': ['Initiator', 'Control', 'Anti-Mobility', 'Immobilize']}],
    'Miya':     [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage']}],
    'Moskov':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'AoE Damage']}],
    # N
    'Nana':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage', 'Support'], 'tags': ['Poke', 'Control', 'Set-up', 'Polymorph']}],
    'Natalia':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Assassin'], 'tags': ['Pick-off', 'Conceal', 'Vision', 'Silence']}],
    'Natan':    [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Mage'], 'tags': ['Late Game', 'Carry', 'Magic Damage', 'Sustain Damage']}],
    'Nolan':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Burst', 'High Mobility', 'Carry']}],
    'Novaria':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'Long Range', 'Vision', 'Map Control', 'Wall Pass']}],
    # O
    'Obsidia':  [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Control', 'AoE Damage', 'Set-up', 'Magic Damage']}],
    'Odette':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Burst', 'Set-up']}],
    # P
    'Paquito':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Burst', 'Early Game', 'Short Dash']}],
    'Pharsa':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Poke', 'Long Range', 'Global Presence', 'High Ground Defense']}],
    'Phoveus':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Anti-Mobility', 'Dive', 'Sustain']}],
    'Popol and Kupa': [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman', 'Support'], 'tags': ['Control', 'Push', 'Vision', 'Stun']}],
    # R
    'Rafaela':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Support'], 'tags': ['Heal', 'Utility', 'High Mobility']}],
    'Roger':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter', 'Marksman'], 'tags': ['Carry', 'Burst', 'Late Game']}],
    'Ruby':     [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Tank'], 'tags': ['Sustain', 'Control', 'Peel']}],
    # S
    'Saber':    [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Assassin'], 'tags': ['Pick-off', 'Burst', 'Single Target CC']}],
    'Selena':   [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Assassin', 'Mage'], 'tags': ['Pick-off', 'Vision', 'Burst', 'Control', 'Stun']}],
    'Silvanna': [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Mage'], 'tags': ['Pick-off', 'Single Target CC', 'Magic Damage']}],
    'Sun':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Split Push', 'Carry', 'Late Game']}],
    # T
    'Terizla':  [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'AoE Damage', 'Set-up']}],
    'Thamuz':   [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Early Game', 'Dive']}],
    'Tigreal':  [{'build_name': 'Standard', 'primary_role': 'Roam', 'sub_role': ['Tank'], 'tags': ['Initiator', 'Set-up', 'Front-line', 'Peel']}],
    # U
    'Uranus':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Tank'], 'tags': ['Sustain', 'Front-line', 'Split Push']}],
    # V
    'Vale':     [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Set-up']}],
    'Valentina':[{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'Utility', 'Magic Damage', 'High Mobility']}],
    'Valir':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'Control', 'Disengage']}],
    'Vexana':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Burst', 'Control']}],
    # W
    'Wanwan':   [{'build_name': 'Standard', 'primary_role': 'Gold', 'sub_role': ['Marksman'], 'tags': ['Late Game', 'Carry', 'High Mobility', 'Immunity']}],
    # X
    'X.Borg':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Sustain', 'Poke', 'AoE Damage']}],
    'Xavier':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Poke', 'AoE Damage', 'Long Range', 'High Ground Defense']}],
    # Y
    'Yi Sun-shin': [{'build_name': 'Standard', 'primary_role': 'Jungle', 'sub_role': ['Marksman', 'Assassin'], 'tags': ['Carry', 'Late Game', 'Global Presence', 'Vision']}],
    'Yin':      [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Pick-off', 'Single Target CC', 'Burst']}],
    'Yu Zhong': [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter'], 'tags': ['Initiator', 'Dive', 'AoE Damage', 'Sustain']}],
    'Yve':      [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['AoE Damage', 'Control', 'Poke', 'Set-up', 'High Ground Defense']}],
    # Z
    'Zhask':    [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Push', 'Poke', 'AoE Damage']}],
    'Zhuxin':   [{'build_name': 'Standard', 'primary_role': 'Mid', 'sub_role': ['Mage'], 'tags': ['Burst', 'AoE Damage', 'Sustain']}],
    'Zilong':   [{'build_name': 'Standard', 'primary_role': 'EXP', 'sub_role': ['Fighter', 'Assassin'], 'tags': ['Split Push', 'Pick-off', 'Late Game']}]
}

HERO_DAMAGE_TYPE = {
    'Aamon': ['Magic'], 'Akai': ['Physical'], 'Aldous': ['Physical'], 'Alice': ['Magic'], 'Alpha': ['Physical'], 
    'Alucard': ['Physical'], 'Angela': ['Magic'], 'Argus': ['Physical'], 'Arlott': ['Physical'], 'Atlas': ['Magic'], 
    'Aulus': ['Physical'], 'Aurora': ['Magic'], 'Badang': ['Physical'], 'Balmond': ['Physical', 'True'], 'Bane': ['Physical', 'Magic'], 
    'Barats': ['Physical'], 'Baxia': ['Magic'], 'Beatrix': ['Physical'], 'Belerick': ['Magic'], 'Benedetta': ['Physical'], 
    'Brody': ['Physical'], 'Bruno': ['Physical'], 'Carmilla': ['Magic'], 'Cecilion': ['Magic'], "Chang'e": ['Magic'], 
    'Chip': ['Magic'], 'Chou': ['Physical'], 'Cici': ['Physical'], 'Claude': ['Physical'], 'Clint': ['Physical'], 
    'Cyclops': ['Magic'], 'Diggie': ['Magic'], 'Dyrroth': ['Physical'], 'Edith': ['Magic'], 'Esmeralda': ['Magic'], 
    'Estes': ['Magic'], 'Eudora': ['Magic'], 'Fanny': ['Physical'], 'Faramis': ['Magic'], 'Floryn': ['Magic'], 
    'Franco': ['Physical'], 'Fredrinn': ['Physical'], 'Freya': ['Physical'], 'Gatotkaca': ['Magic'], 'Gloo': ['Magic'], 
    'Gord': ['Magic'], 'Granger': ['Physical'], 'Grock': ['Physical'], 'Guinevere': ['Magic'], 'Gusion': ['Magic'], 
    'Hanabi': ['Physical'], 'Hanzo': ['Physical'], 'Harith': ['Magic'], 'Harley': ['Magic'], 'Hayabusa': ['Physical'], 
    'Helcurt': ['Physical'], 'Hilda': ['Physical'], 'Hylos': ['Magic'], 'Irithel': ['Physical'], 'Ixia': ['Physical'], 
    'Jawhead': ['Physical'], 'Johnson': ['Magic'], 'Joy': ['Magic'], 'Julian': ['Magic'], 'Kadita': ['Magic'], 'Kagura': ['Magic'], 
    'Kaja': ['Magic'], 'Karina': ['Magic', 'True'], 'Karrie': ['Physical', 'True'], 'Khaleed': ['Physical'], 'Khufra': ['Physical'], 
    'Kimmy': ['Physical', 'Magic'], 'Lancelot': ['Physical'], 'Lapu-Lapu': ['Physical'], 'Layla': ['Physical'], 'Leomord': ['Physical'], 
    'Lesley': ['Physical', 'True'], 'Ling': ['Physical'], 'Lolita': ['Physical'], 'Lunox': ['Magic'], 'Luo Yi': ['Magic'], 
    'Lylia': ['Magic'], 'Martis': ['Physical', 'True'], 'Masha': ['Physical'], 'Mathilda': ['Magic'], 'Melissa': ['Physical'], 
    'Minotaur': ['Physical'], 'Minsitthar': ['Physical'], 'Miya': ['Physical'], 'Moskov': ['Physical'], 
    'Nana': ['Magic'], 'Natalia': ['Physical'], 'Natan': ['Magic'], 'Nolan': ['Physical'], 'Novaria': ['Magic'], 
    'Obsidia': ['Magic'], 'Odette': ['Magic'], 'Paquito': ['Physical'], 'Pharsa': ['Magic'], 'Phoveus': ['Magic'], 'Popol and Kupa': ['Physical'], 
    'Rafaela': ['Magic'], 'Roger': ['Physical'], 'Ruby': ['Physical'], 'Saber': ['Physical'], 'Selena': ['Magic'], 
    'Silvanna': ['Magic'], 'Sun': ['Physical'], 'Terizla': ['Physical'], 'Thamuz': ['Physical', 'True'], 'Tigreal': ['Physical'], 
    'Uranus': ['Magic'], 'Vale': ['Magic'], 'Valentina': ['Magic'], 'Valir': ['Magic'], 'Vexana': ['Magic'], 
    'Wanwan': ['Physical'], 'X.Borg': ['Physical', 'True'], 'Xavier': ['Magic'], 'Yi Sun-shin': ['Physical'], 'Yin': ['Physical'], 
    'Yu Zhong': ['Physical'], 'Yve': ['Magic'], 'Zhask': ['Magic'], 'Zhuxin': ['Magic'], 'Zilong': ['Physical']
}

ALL_HERO_NAMES = sorted(list(HERO_PROFILES.keys()))
all_hero_options = [("---", None)] + [(name, name) for name in ALL_HERO_NAMES]
main_team_options = [("(Generic Blue)", "Blue Team"), ("(Generic Red)", "Red Team")]
position_labels = ["EXP", "Jungle", "Mid", "Gold", "Roam"]

# ===================================================================
# SECTION 3: CACHED FUNCTIONS FOR EFFICIENCY
# ===================================================================

@st.cache_resource
def load_draft_model():
    """Loads the post-draft prediction model from disk."""
    try:
        return joblib.load('draft_predictor.joblib')
    except FileNotFoundError:
        return None

# ===================================================================
# SECTION 4: HELPER AND LOGIC FUNCTIONS
# ===================================================================

def generate_bar_html(probability, title, t1_name="Blue", t2_name="Red"):
    if probability is None: return ""
    blue_pct = int(probability * 100)
    red_pct = 100 - blue_pct
    return f"""
    <p style="margin: 0 0 4px 0; font-size: 0.9em; color: #555; font-weight:bold;">{title}</p>
    <div style="display: flex; width: 100%; height: 28px; font-weight: bold; font-size: 14px; border-radius: 5px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);">
        <div style="width: {blue_pct}%; background-color: #4299e1; color: white; display: flex; align-items: center; justify-content: center;">{t1_name}: {blue_pct}%</div>
        <div style="width: {red_pct}%; background-color: #f56565; color: white; display: flex; align-items: center; justify-content: center;">{t2_name}: {red_pct}%</div>
    </div>
    """

def calculate_series_score_probs(p_win_game, series_format=3):
    if p_win_game is None or not (0 <= p_win_game <= 1): return {}
    p = p_win_game
    q = 1 - p
    
    if series_format == 2:
        return {"2-0": p**2, "1-1": 2 * p * q, "0-2": q**2}
    
    wins_needed = math.ceil((series_format + 1) / 2)
    results = {}
    
    for losses in range(wins_needed):
        games_played = wins_needed + losses
        if games_played > series_format: continue
        combinations = math.comb(games_played - 1, wins_needed - 1)
        prob = combinations * (p ** wins_needed) * (q ** losses)
        results[f"{wins_needed}-{losses}"] = prob

    for losses in range(wins_needed):
        games_played = wins_needed + losses
        if games_played > series_format: continue
        combinations = math.comb(games_played - 1, wins_needed - 1)
        prob = combinations * (q ** wins_needed) * (p ** losses)
        results[f"{losses}-{wins_needed}"] = prob
        
    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))

def predict_draft_outcome(blue_picks, red_picks, blue_team, red_team, model_assets, data_for_explanation):
    # This is a placeholder. You need the real function from your notebook.
    st.warning("`predict_draft_outcome` function is a placeholder. Please paste the real function.")
    return 0.5, 0.5, {'blue': ["Analysis requires the full function."], 'red': ["Analysis requires the full function."]}

# ===================================================================
# SECTION 5: MAIN APPLICATION UI
# ===================================================================

st.title("🎯 Professional Drafting Assistant")

draft_model_assets = load_draft_model()

if not draft_model_assets:
    st.error("`draft_predictor.joblib` not found. Please ensure the model file is in the same folder as app.py.")
    st.stop()

if 'draft' not in st.session_state:
    st.session_state.draft = {
        'blue_team': main_team_options[0][1], 
        'red_team': main_team_options[1][1],
        'blue_bans': [None] * 5, 'red_bans': [None] * 5,
        'blue_picks': {role: None for role in position_labels},
        'red_picks': {role: None for role in position_labels},
    }

series_format = st.selectbox(
    'Series Format:', 
    options=[1, 2, 3, 5, 7], 
    format_func=lambda x: f"Best-of-{x}",
    index=2
)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("Blue Team")
    st.selectbox("Team:", options=main_team_options, key='blue_team_select')
    
    st.subheader("Bans")
    ban_cols = st.columns(5)
    for i in range(5):
        st.selectbox(f"B{i+1}", options=all_hero_options, key=f"b_ban_{i}", label_visibility="collapsed")
    
    st.subheader("Picks")
    for role in position_labels:
        st.selectbox(role, options=all_hero_options, key=f"b_pick_{role}")

with col2:
    st.header("Red Team")
    st.selectbox("Team:", options=main_team_options, key='r_team_select')

    st.subheader("Bans")
    ban_cols = st.columns(5)
    for i in range(5):
        st.selectbox(f"B{i+1}", options=all_hero_options, key=f"r_ban_{i}", label_visibility="collapsed")
    
    st.subheader("Picks")
    for role in position_labels:
        st.selectbox(role, options=all_hero_options, key=f"r_pick_{role}")

st.markdown("---")
st.header("Live Analysis")

blue_picks_dict = {k: st.session_state[f"b_pick_{k}"] for k in position_labels if st.session_state[f"b_pick_{k}"] is not None and st.session_state[f"b_pick_{k}"] != "---"}
red_picks_dict = {k: st.session_state[f"r_pick_{k}"] for k in position_labels if st.session_state[f"r_pick_{k}"] is not None and st.session_state[f"r_pick_{k}"] != "---"}
blue_team_name = st.session_state['blue_team_select']
red_team_name = st.session_state['r_team_select']

if blue_picks_dict or red_picks_dict:
    win_prob_overall, win_prob_draft_only, explanation_dict = predict_draft_outcome(
        blue_picks_dict, red_picks_dict, blue_team_name, red_team_name, draft_model_assets, {}
    )

    st.markdown(generate_bar_html(win_prob_overall, "Overall Prediction (Draft + Team History)", blue_team_name, red_team_name), unsafe_allow_html=True)
    st.markdown(generate_bar_html(win_prob_draft_only, "Draft-Only Prediction"), unsafe_allow_html=True)

    series_probs = calculate_series_score_probs(win_prob_overall, series_format)
    if series_probs:
        st.subheader(f"Best-of-{series_format} Series Score Probability")
        html = "<ul>"
        for score, probability in series_probs.items():
            try:
                t1_score, t2_score = map(int, score.split('-'))
                if score == "1-1":
                     winner_html = f"<b style='color:grey;'>Draw {score}:</b>"
                elif t1_score > t2_score:
                    winner_html = f"<b style='color:#4299e1;'>{blue_team_name} wins {score}:</b>"
                else:
                    winner_html = f"<b style='color:#f56565;'>{red_team_name} wins {score}:</b>"
                html += f"<li>{winner_html} {probability:.1%}</li>"
            except ValueError:
                continue 
        html += "</ul>"
        st.markdown(html, unsafe_allow_html=True)

    st.subheader("Draft Analysis")
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.markdown("<h6>Blue Team</h6>", unsafe_allow_html=True)
        for point in explanation_dict.get('blue', []):
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
    with exp_col2:
        st.markdown("<h6>Red Team</h6>", unsafe_allow_html=True)
        for point in explanation_dict.get('red', []):
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
else:
    st.info("Make a selection in the draft to see the live analysis.")

st.sidebar.title("AI Suggestions")
st.sidebar.info("This feature is under construction.")