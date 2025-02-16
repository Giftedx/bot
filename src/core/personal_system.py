import json
from pathlib import Path
from datetime import datetime, timedelta
import random
import logging
from typing import Dict, List, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PersonalSystem:
    """Core system for managing personal content and cross-game features"""
    
    def __init__(self):
        self.data_dir = Path("src/data")
        self.personal_data = self._load_data("personal/personal_content.json")
        self.events_data = self._load_data("events/cross_game_events.json")
        self.hidden_data = self._load_data("hidden/hidden_content.json")
        
        # Runtime state
        self.active_events = {}
        self.player_states = {}
        self.watch_history = {}
        self.achievement_progress = {}
        self.pet_states = {}
        
        # Initialize subsystems
        self.pet_manager = PetManager(self)
        self.watch_tracker = WatchTracker(self)
        self.achievement_manager = AchievementManager(self)
        self.event_manager = EventManager(self)
        self.joke_manager = JokeManager(self)
    
    def _load_data(self, relative_path: str) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.data_dir / relative_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {relative_path}: {e}")
            return {}
    
    def initialize_player(self, player_name: str) -> None:
        """Initialize or load player state"""
        if player_name not in self.player_states:
            self.player_states[player_name] = {
                'pets': {},
                'achievements': {},
                'watch_history': {},
                'active_effects': {},
                'unlocked_content': set(),
                'special_titles': set(),
                'last_seen': datetime.now().isoformat()
            }
            
            # Check for exclusive pets
            self._check_exclusive_pets(player_name)
    
    def _check_exclusive_pets(self, player_name: str) -> None:
        """Check and grant any exclusive pets for the player"""
        exclusive_pets = self.personal_data['personal_pets']['exclusive_pets']
        
        for pet_name, pet_data in exclusive_pets.items():
            if self._evaluate_condition(pet_data['unlock_condition'], {'account_name': player_name}):
                self.pet_manager.grant_pet(player_name, pet_name, pet_data)
                logger.info(f"Granted exclusive pet {pet_name} to {player_name}")
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition string"""
        try:
            # Convert condition string to actual check
            if '==' in condition:
                var, val = condition.split('==')
                return context.get(var.strip()) == eval(val.strip())
            elif 'in' in condition:
                var, val = condition.split('in')
                return context.get(var.strip()) in eval(val.strip())
            return False
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False

class PetManager:
    """Manages pet-related functionality"""
    
    def __init__(self, system: PersonalSystem):
        self.system = system
        self.pet_states = {}
    
    def grant_pet(self, player_name: str, pet_name: str, pet_data: Dict[str, Any]) -> None:
        """Grant a pet to a player"""
        if player_name not in self.pet_states:
            self.pet_states[player_name] = {}
            
        self.pet_states[player_name][pet_name] = {
            'data': pet_data,
            'stats': {
                'happiness': 100,
                'loyalty': 0,
                'experience': 0
            },
            'abilities': {
                name: {'unlocked': False, 'level': 0}
                for name in pet_data['abilities'].keys()
            },
            'last_interaction': datetime.now().isoformat()
        }
    
    def interact_with_pet(self, player_name: str, pet_name: str, interaction_type: str) -> Dict[str, Any]:
        """Process a pet interaction"""
        if not self._validate_interaction(player_name, pet_name):
            return {'success': False, 'message': 'Invalid interaction'}
            
        pet_state = self.pet_states[player_name][pet_name]
        interaction = self.system.personal_data['personal_pets']['pet_interactions'].get(interaction_type)
        
        if not interaction:
            return {'success': False, 'message': 'Invalid interaction type'}
            
        # Process interaction effects
        results = self._process_interaction_effects(pet_state, interaction)
        
        # Check for special events
        special_event = self._check_special_events(player_name, pet_name, interaction_type)
        if special_event:
            results['special_event'] = special_event
            
        # Update pet state
        self._update_pet_state(pet_state)
        
        return results
    
    def _validate_interaction(self, player_name: str, pet_name: str) -> bool:
        """Validate that a player can interact with a pet"""
        return (player_name in self.pet_states and 
                pet_name in self.pet_states[player_name])
    
    def _process_interaction_effects(self, pet_state: Dict[str, Any], interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Process the effects of a pet interaction"""
        results = {
            'success': True,
            'effects': [],
            'messages': []
        }
        
        # Apply interaction effects
        if 'effect' in interaction:
            effect_result = self._apply_effect(pet_state, interaction['effect'])
            results['effects'].append(effect_result)
            
        # Update stats
        self._update_stats(pet_state)
        
        # Check for ability unlocks
        new_abilities = self._check_ability_unlocks(pet_state)
        if new_abilities:
            results['new_abilities'] = new_abilities
            
        return results
    
    def _apply_effect(self, pet_state: Dict[str, Any], effect: str) -> Dict[str, Any]:
        """Apply a specific effect to a pet"""
        effect_result = {
            'type': effect,
            'success': True,
            'changes': {}
        }
        
        if 'home_guard' in effect:
            effect_result['changes']['defense_bonus'] = 10
        elif 'fierce_bark' in effect:
            effect_result['changes']['intimidation'] = random.random() < 0.3
            
        return effect_result
    
    def _update_stats(self, pet_state: Dict[str, Any]) -> None:
        """Update pet stats based on interaction"""
        stats = pet_state['stats']
        stats['happiness'] = min(100, stats['happiness'] + 5)
        stats['loyalty'] = min(100, stats['loyalty'] + 1)
        stats['experience'] += 10
    
    def _check_ability_unlocks(self, pet_state: Dict[str, Any]) -> List[str]:
        """Check and unlock new abilities"""
        new_abilities = []
        for ability_name, ability_data in pet_state['abilities'].items():
            if not ability_data['unlocked']:
                if self._can_unlock_ability(pet_state, ability_name):
                    ability_data['unlocked'] = True
                    new_abilities.append(ability_name)
        return new_abilities
    
    def _can_unlock_ability(self, pet_state: Dict[str, Any], ability_name: str) -> bool:
        """Check if an ability can be unlocked"""
        stats = pet_state['stats']
        if ability_name == 'home_guard':
            return stats['loyalty'] >= 50
        elif ability_name == 'fierce_bark':
            return stats['experience'] >= 1000
        return False
    
    def _check_special_events(self, player_name: str, pet_name: str, interaction_type: str) -> Optional[Dict[str, Any]]:
        """Check for special pet events"""
        pet_data = self.pet_states[player_name][pet_name]['data']
        
        # Check for Bella's protection event
        if pet_name == 'bella' and random.random() < 0.01:
            return {
                'type': 'bella_guardian',
                'message': "A Yorkshire Terrier growls at the ban system",
                'effect': 'temporary_ban_immunity'
            }
            
        # Check for cat duo event
        if pet_name in ['pumpkin', 'cheddar']:
            other_cat = 'cheddar' if pet_name == 'pumpkin' else 'pumpkin'
            if other_cat in self.pet_states[player_name]:
                if random.random() < 0.05:
                    return {
                        'type': 'cat_duo',
                        'message': "The cats of Mull combine their powers!",
                        'effect': 'mull_blessing'
                    }
        
        return None

class WatchTracker:
    """Tracks Plex watch history and rewards"""
    
    def __init__(self, system: PersonalSystem):
        self.system = system
        self.watch_history = {}
        self.active_rewards = {}
    
    def record_watch(self, player_name: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a watch session and process rewards"""
        if player_name not in self.watch_history:
            self.watch_history[player_name] = []
            
        # Add watch record
        watch_record = {
            'content_id': content_data['id'],
            'type': content_data['type'],
            'title': content_data['title'],
            'timestamp': datetime.now().isoformat(),
            'duration': content_data.get('duration', 0)
        }
        self.watch_history[player_name].append(watch_record)
        
        # Process rewards
        rewards = self._process_watch_rewards(player_name, content_data)
        
        # Check for special challenges
        challenges = self._check_watch_challenges(player_name, content_data)
        
        return {
            'success': True,
            'rewards': rewards,
            'challenges': challenges
        }
    
    def _process_watch_rewards(self, player_name: str, content_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process rewards for watching content"""
        rewards = []
        
        # Check streak rewards
        streak_reward = self._check_streak_reward(player_name)
        if streak_reward:
            rewards.append(streak_reward)
            
        # Check genre bonuses
        genre_bonus = self._check_genre_bonus(content_data.get('genre'))
        if genre_bonus:
            rewards.append(genre_bonus)
            
        # Check special content rewards
        content_reward = self._check_content_specific_reward(content_data)
        if content_reward:
            rewards.append(content_reward)
            
        return rewards
    
    def _check_streak_reward(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Check and grant streak rewards"""
        streak_data = self._calculate_streak(player_name)
        streak_rewards = self.system.personal_data['plex_rewards']['watch_streaks']['daily_rewards']
        
        if streak_data['days'] >= 7:
            return streak_rewards['weekly']
        elif streak_data['days'] >= 3:
            return streak_rewards['three_days']
            
        return None
    
    def _calculate_streak(self, player_name: str) -> Dict[str, Any]:
        """Calculate a player's watch streak"""
        if not self.watch_history.get(player_name):
            return {'days': 0, 'active': False}
            
        watches = sorted(self.watch_history[player_name], key=lambda x: x['timestamp'])
        current_date = datetime.now()
        streak_days = 0
        last_date = None
        
        for watch in reversed(watches):
            watch_date = datetime.fromisoformat(watch['timestamp']).date()
            
            if last_date is None:
                last_date = watch_date
                streak_days = 1
            elif (last_date - watch_date).days == 1:
                streak_days += 1
                last_date = watch_date
            else:
                break
                
        return {
            'days': streak_days,
            'active': (current_date.date() - last_date).days <= 1 if last_date else False
        }
    
    def _check_genre_bonus(self, genre: Optional[str]) -> Optional[Dict[str, Any]]:
        """Check and grant genre-specific bonuses"""
        if not genre:
            return None
            
        genre_bonuses = self.system.personal_data['plex_rewards']['genre_bonuses']
        if genre.lower() in genre_bonuses:
            return genre_bonuses[genre.lower()]
            
        return None
    
    def _check_content_specific_reward(self, content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for content-specific rewards"""
        content_rewards = self.system.personal_data['plex_rewards']['content_specific']
        
        # Check movies
        if content_data['type'] == 'movie':
            for challenge, data in content_rewards['movie_challenges'].items():
                if self._meets_challenge_requirements(content_data, data['requirement']):
                    return {
                        'type': 'movie_reward',
                        'challenge': challenge,
                        'reward': data['reward'],
                        'effects': data['effects']
                    }
        
        # Check series
        elif content_data['type'] == 'episode':
            for challenge, data in content_rewards['series_challenges'].items():
                if self._meets_challenge_requirements(content_data, data['requirement']):
                    return {
                        'type': 'series_reward',
                        'challenge': challenge,
                        'reward': data['reward'],
                        'effects': data['effects']
                    }
        
        return None
    
    def _meets_challenge_requirements(self, content_data: Dict[str, Any], requirement: str) -> bool:
        """Check if content meets challenge requirements"""
        if requirement == 'watch_extended_trilogy':
            return self._check_trilogy_completion(content_data, extended=True)
        elif requirement == 'watch_trilogy':
            return self._check_trilogy_completion(content_data)
        elif requirement == 'complete_series':
            return self._check_series_completion(content_data)
            
        return False
    
    def _check_trilogy_completion(self, content_data: Dict[str, Any], extended: bool = False) -> bool:
        """Check if a trilogy has been completed"""
        # Implementation would check for all parts of trilogy in watch history
        return False
    
    def _check_series_completion(self, content_data: Dict[str, Any]) -> bool:
        """Check if a series has been completed"""
        # Implementation would check if all episodes have been watched
        return False

class AchievementManager:
    """Manages achievements and meta-challenges"""
    
    def __init__(self, system: PersonalSystem):
        self.system = system
        self.achievement_progress = {}
    
    def check_achievements(self, player_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for achievement completions"""
        unlocked = []
        
        # Check meta achievements
        meta_unlocked = self._check_meta_achievements(player_name, context)
        unlocked.extend(meta_unlocked)
        
        # Check hidden achievements
        hidden_unlocked = self._check_hidden_achievements(player_name, context)
        unlocked.extend(hidden_unlocked)
        
        return unlocked
    
    def _check_meta_achievements(self, player_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check meta achievement completions"""
        unlocked = []
        meta_achievements = self.system.personal_data['meta_challenges']['cross_media_challenges']
        
        for achievement_id, data in meta_achievements.items():
            if self._check_achievement_requirements(player_name, data['requirements'], context):
                unlocked.append({
                    'id': achievement_id,
                    'type': 'meta',
                    'name': data.get('name', achievement_id),
                    'reward': data['reward'],
                    'effects': data['effects']
                })
                
        return unlocked
    
    def _check_hidden_achievements(self, player_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check hidden achievement completions"""
        unlocked = []
        hidden_achievements = self.system.personal_data['meta_challenges']['hidden_achievements']
        
        for achievement_id, data in hidden_achievements.items():
            if self._check_achievement_trigger(data['trigger'], context):
                unlocked.append({
                    'id': achievement_id,
                    'type': 'hidden',
                    'response': data['response'],
                    'reward': data['reward']
                })
                
        return unlocked
    
    def _check_achievement_requirements(self, player_name: str, requirements: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if achievement requirements are met"""
        for req_type, req_value in requirements.items():
            if not self._check_single_requirement(player_name, req_type, req_value, context):
                return False
        return True
    
    def _check_single_requirement(self, player_name: str, req_type: str, req_value: Any, context: Dict[str, Any]) -> bool:
        """Check a single achievement requirement"""
        if req_type == 'watch':
            return self.system.watch_tracker._meets_challenge_requirements(context, req_value)
        elif req_type == 'achieve':
            return self._check_game_achievement(player_name, req_value)
        elif req_type == 'craft':
            return self._check_crafting_achievement(player_name, req_value)
            
        return False
    
    def _check_achievement_trigger(self, trigger: str, context: Dict[str, Any]) -> bool:
        """Check if an achievement trigger condition is met"""
        if trigger == 'catch_someone_botting':
            return context.get('detected_botting', False)
        elif trigger == 'write_passionate_complaint':
            return self._check_complaint_quality(context.get('message', ''))
            
        return False
    
    def _check_complaint_quality(self, message: str) -> bool:
        """Check if a complaint message meets quality standards"""
        # Implementation would check message length, keywords, formatting, etc.
        return False

class EventManager:
    """Manages cross-game events and special occurrences"""
    
    def __init__(self, system: PersonalSystem):
        self.system = system
        self.active_events = {}
    
    def update_events(self) -> List[Dict[str, Any]]:
        """Update active events and check for new ones"""
        new_events = []
        
        # Check random events
        random_events = self._check_random_events()
        new_events.extend(random_events)
        
        # Check scheduled events
        scheduled_events = self._check_scheduled_events()
        new_events.extend(scheduled_events)
        
        # Process environmental effects
        self._update_environmental_effects()
        
        return new_events
    
    def _check_random_events(self) -> List[Dict[str, Any]]:
        """Check for random event triggers"""
        new_events = []
        random_events = self.system.events_data['world_events']['random_events']
        
        for event_id, data in random_events.items():
            if random.random() < data['trigger_chance']:
                new_events.append(self._start_event(event_id, data))
                
        return new_events
    
    def _check_scheduled_events(self) -> List[Dict[str, Any]]:
        """Check for scheduled event triggers"""
        new_events = []
        scheduled_events = self.system.events_data['world_events']['scheduled_events']
        
        current_time = datetime.now()
        
        # Check weekly rotation
        if self._should_start_weekly_event(current_time):
            new_events.append(self._start_weekly_rotation())
            
        # Check monthly special
        if self._should_start_monthly_event(current_time):
            new_events.append(self._start_monthly_special())
            
        return new_events
    
    def _update_environmental_effects(self) -> None:
        """Update environmental effects across games"""
        weather = self._get_current_weather()
        day_night = self._get_day_night_cycle()
        
        self._apply_weather_effects(weather)
        self._apply_day_night_effects(day_night)
    
    def _start_event(self, event_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new event"""
        event = {
            'id': event_id,
            'type': data.get('type', 'random'),
            'start_time': datetime.now().isoformat(),
            'duration': data.get('duration', '1h'),
            'effects': data.get('effects', []),
            'active': True
        }
        
        self.active_events[event_id] = event
        return event
    
    def _should_start_weekly_event(self, current_time: datetime) -> bool:
        """Check if a new weekly event should start"""
        # Implementation would check last weekly event and time
        return False
    
    def _should_start_monthly_event(self, current_time: datetime) -> bool:
        """Check if a new monthly event should start"""
        # Implementation would check last monthly event and time
        return False
    
    def _get_current_weather(self) -> Dict[str, Any]:
        """Get current weather state"""
        # Implementation would determine current weather
        return {'type': 'clear', 'intensity': 1.0}
    
    def _get_day_night_cycle(self) -> Dict[str, Any]:
        """Get current day/night cycle state"""
        # Implementation would determine current cycle
        return {'phase': 'day', 'progress': 0.5}

class JokeManager:
    """Manages jokes, references, and easter eggs"""
    
    def __init__(self, system: PersonalSystem):
        self.system = system
        self.triggered_jokes = set()
    
    def check_triggers(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for joke triggers"""
        # Check chat triggers
        chat_joke = self._check_chat_triggers(context)
        if chat_joke:
            return chat_joke
            
        # Check rare events
        rare_event = self._check_rare_events(context)
        if rare_event:
            return rare_event
            
        return None
    
    def _check_chat_triggers(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for chat-based joke triggers"""
        message = context.get('message', '').lower()
        player = context.get('player')
        
        # Check Gary-related triggers
        if player == 'ThePanj' and 'afk' in message:
            return self._trigger_gary_joke()
            
        # Check support-related triggers
        if 'banned' in message or 'support' in message:
            return self._trigger_support_joke()
            
        # Check Mull-related triggers
        if 'mull' in message or 'cat' in message:
            return self._trigger_mull_reference()
            
        return None
    
    def _check_rare_events(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for rare event triggers"""
        rare_events = self.system.personal_data['hidden_jokes']['rare_events']
        
        for event_id, data in rare_events.items():
            if random.random() < data['trigger_chance']:
                return {
                    'type': 'rare_event',
                    'id': event_id,
                    'message': data['message'],
                    'effect': data['effect']
                }
                
        return None
    
    def _trigger_gary_joke(self) -> Dict[str, Any]:
        """Trigger a Gary-related joke"""
        gary_excuses = self.system.personal_data['hidden_jokes']['chat_triggers']['gary_excuses']
        return {
            'type': 'gary_joke',
            'message': random.choice(gary_excuses)
        }
    
    def _trigger_support_joke(self) -> Dict[str, Any]:
        """Trigger a support-related joke"""
        support_jokes = self.system.personal_data['hidden_jokes']['chat_triggers']['support_tickets']
        return {
            'type': 'support_joke',
            'message': random.choice(support_jokes)
        }
    
    def _trigger_mull_reference(self) -> Dict[str, Any]:
        """Trigger a Mull-related reference"""
        mull_references = self.system.personal_data['hidden_jokes']['chat_triggers']['mull_references']
        return {
            'type': 'mull_reference',
            'message': random.choice(mull_references)
        }

if __name__ == "__main__":
    # Example usage
    system = PersonalSystem()
    
    # Initialize some players
    system.initialize_player("Haggis")
    system.initialize_player("ThePanj")
    system.initialize_player("PeachComfort")
    
    # Test pet interaction
    result = system.pet_manager.interact_with_pet("Haggis", "bella", "pet")
    print("Pet interaction result:", result)
    
    # Test watch tracking
    watch_result = system.watch_tracker.record_watch("Haggis", {
        'id': '123',
        'type': 'movie',
        'title': 'The Lord of the Rings: The Fellowship of the Ring',
        'duration': 10800  # 3 hours
    })
    print("Watch result:", watch_result)
    
    # Test joke system
    joke = system.joke_manager.check_triggers({
        'message': "I think I got banned unfairly",
        'player': "Haggis"
    })
    print("Joke trigger:", joke) 