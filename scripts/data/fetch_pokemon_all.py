import requests
import json
from pathlib import Path
import pokepy
import pokebase as pb
from pokemon_tcg_sdk import Card, Set, Type
from datetime import datetime

def fetch_pokemon_data():
    """
    Fetches comprehensive Pokemon data from multiple sources:
    - PokeAPI (base Pokemon data)
    - Pokemon TCG API (card data)
    - Custom game mechanics data
    """
    pokemon_data = {
        'timestamp': datetime.now().isoformat(),
        'pokeapi': {},
        'tcg': {},
        'custom': {
            'battle_mechanics': fetch_battle_mechanics(),
            'pet_system': fetch_pet_mechanics(),
            'evolution_chains': fetch_evolution_chains()
        }
    }
    
    # Fetch from PokeAPI
    try:
        client = pokepy.V2Client()
        # Get all Pokemon up to current generation
        for pokemon_id in range(1, 899):  # Adjust range as needed
            try:
                pokemon = client.get_pokemon(pokemon_id)
                pokemon_species = client.get_pokemon_species(pokemon_id)
                
                pokemon_data['pokeapi'][pokemon_id] = {
                    'name': pokemon.name,
                    'types': [t.type.name for t in pokemon.types],
                    'stats': {s.stat.name: s.base_stat for s in pokemon.stats},
                    'abilities': [a.ability.name for a in pokemon.abilities],
                    'moves': [m.move.name for m in pokemon.moves],
                    'sprites': {
                        'front_default': pokemon.sprites.front_default,
                        'back_default': pokemon.sprites.back_default
                    },
                    'species_data': {
                        'base_happiness': pokemon_species.base_happiness,
                        'capture_rate': pokemon_species.capture_rate,
                        'growth_rate': pokemon_species.growth_rate.name,
                        'habitat': pokemon_species.habitat.name if pokemon_species.habitat else None
                    }
                }
            except Exception as e:
                print(f"Error fetching Pokemon {pokemon_id}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error initializing PokeAPI client: {str(e)}")
    
    # Fetch from Pokemon TCG API
    try:
        # Get recent sets
        sets = Set.where(orderBy='-releaseDate')
        for set_data in sets[:10]:  # Get last 10 sets
            cards = Card.where(q=f'set.id:{set_data.id}')
            pokemon_data['tcg'][set_data.id] = {
                'set_name': set_data.name,
                'release_date': set_data.releaseDate,
                'cards': [{
                    'id': card.id,
                    'name': card.name,
                    'supertype': card.supertype,
                    'subtypes': card.subtypes,
                    'hp': card.hp if hasattr(card, 'hp') else None,
                    'types': card.types if hasattr(card, 'types') else None,
                    'attacks': card.attacks if hasattr(card, 'attacks') else None
                } for card in cards]
            }
    except Exception as e:
        print(f"Error fetching TCG data: {str(e)}")
    
    # Save the data
    output_dir = Path("src/data/pokemon")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "pokemon_data.json", 'w') as f:
        json.dump(pokemon_data, f, indent=4)
    
    return pokemon_data

def fetch_battle_mechanics():
    """Fetch custom battle mechanics data"""
    return {
        'status_effects': {
            'asleep': {'duration': '1-3 turns', 'effect': 'Cannot move'},
            'frozen': {'duration': 'Until thawed', 'effect': 'Cannot move'},
            'burned': {'duration': 'Until cured', 'effect': 'Damage over time'},
            'paralyzed': {'duration': 'Until cured', 'effect': 'May not move'},
            'poisoned': {'duration': 'Until cured', 'effect': 'Damage over time'}
        },
        'type_effectiveness': {
            'normal': {'weaknesses': ['fighting'], 'resistances': [], 'immunities': ['ghost']},
            'fire': {'weaknesses': ['water', 'ground', 'rock'], 'resistances': ['fire', 'grass', 'ice', 'bug', 'steel', 'fairy'], 'immunities': []},
            # ... more types ...
        },
        'critical_rates': {
            'base': 0.0625,
            'high_ratio': 0.125,
            'focus_energy': 0.25
        },
        'weather_effects': {
            'rain': {'water': 1.5, 'fire': 0.5},
            'sun': {'fire': 1.5, 'water': 0.5},
            'sandstorm': {'rock': 1.5},
            'hail': {'ice': 1.5}
        }
    }

def fetch_pet_mechanics():
    """Fetch custom pet system mechanics"""
    return {
        'happiness': {
            'max': 100,
            'decay_rate': 1,  # per day
            'boost_items': {
                'treat': 5,
                'toy': 10,
                'premium_food': 15
            }
        },
        'training': {
            'max_level': 50,
            'experience_curve': 'medium_fast',
            'stat_gains': {
                'attack': [1, 2, 3],
                'defense': [1, 2, 3],
                'speed': [1, 2, 3]
            }
        },
        'evolution': {
            'happiness_threshold': 80,
            'level_requirements': {
                'basic': 16,
                'intermediate': 32,
                'advanced': 48
            }
        },
        'abilities': {
            'companion': {'effect': 'Follows owner in Discord', 'unlock_level': 10},
            'battle_ready': {'effect': 'Can participate in battles', 'unlock_level': 20},
            'treasure_hunter': {'effect': 'Can find rare items', 'unlock_level': 30}
        }
    }

def fetch_evolution_chains():
    """Fetch custom evolution chain data"""
    return {
        'standard': {
            'stages': 3,
            'level_based': True,
            'item_based': False
        },
        'branching': {
            'stages': 2,
            'conditions': ['level', 'item', 'happiness'],
            'branches': 2
        },
        'special': {
            'trade_evolution': True,
            'friendship_evolution': True,
            'time_based_evolution': True
        }
    }

if __name__ == "__main__":
    fetch_pokemon_data() 