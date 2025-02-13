# Critical Components Addendum

## 1. Discord Bot Integration

### Architecture and Components
```
Discord Bot Service
├── core/
│   ├── bot.py           # Main bot class
│   ├── cog_loader.py    # Dynamic cog loading
│   └── event_handler.py # Discord event handling
├── cogs/
│   ├── task_cog.py      # Task management commands
│   ├── plex_cog.py      # Plex integration commands
│   └── pets_cog.py      # Battle pets commands
└── services/
    ├── discord_service.py # Discord API wrapper
    ├── command_parser.py  # Command parsing
    └── message_handler.py # Message processing
```

### Service Definition
```python
class DiscordService(BaseService):
    def __init__(self, config: Config):
        self.token = config.discord_token
        self.client = discord.Client(intents=discord.Intents.all())
        self.command_prefix = config.command_prefix
        self._setup_events()

    async def _setup_events(self):
        @self.client.event
        async def on_ready():
            logger.info("Discord bot ready")

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            await self.handle_message(message)

    async def handle_message(self, message):
        if not message.content.startswith(self.command_prefix):
            return
        # Command handling logic
```

### Integration Points
1. Task Management:
   ```python
   @commands.command()
   async def create_task(self, ctx, *, task_description: str):
       task = await self.task_service.create_task({
           'description': task_description,
           'created_by': ctx.author.id
       })
       await ctx.send(f"Task created: {task.id}")
   ```

2. Plex Integration:
   ```python
   @commands.command()
   async def play_media(self, ctx, *, media_name: str):
       result = await self.plex_service.play_media(media_name)
       await ctx.send(f"Playing: {result.title}")
   ```

## 2. Plex Service Implementation

### Service Definition
```python
class PlexService(BaseService):
    def __init__(self, config: Config):
        self.base_url = config.plex_base_url
        self.token = config.plex_token
        self.server: Optional[PlexServer] = None

    async def initialize(self) -> None:
        try:
            self.server = PlexServer(self.base_url, self.token)
            await self.health_check()
        except Exception as e:
            logger.error(f"Plex initialization failed: {str(e)}")
            raise ServiceError("Plex initialization failed")

    async def search_media(self, query: str) -> List[Media]:
        results = self.server.search(query)
        return [self._convert_to_media(r) for r in results]

    async def play_media(self, media_id: str) -> PlaybackResult:
        client = self._get_active_client()
        media = self.server.fetchItem(int(media_id))
        client.playMedia(media)
        return PlaybackResult(status="playing", media_id=media_id)
```

## 3. Data Migration Strategy

### Phase 1: Analysis and Preparation
1. Analyze existing data:
   ```python
   class DataAnalyzer:
       async def analyze_existing_data(self):
           """Analyze current data structures"""
           existing_tables = await self.db.fetch_all("""
               SELECT table_name, column_name, data_type 
               FROM information_schema.columns
               WHERE table_schema = 'public'
           """)
           return self._generate_migration_plan(existing_tables)
   ```

2. Create migration mappings:
   ```python
   MIGRATION_MAPPINGS = {
       'old_tasks': {
           'target_table': 'tasks',
           'field_mappings': {
               'task_id': 'id',
               'task_desc': 'description',
               'assigned': 'assigned_to'
           }
       },
       'battle_pets': {
           'target_table': 'pets',
           'field_mappings': {
               'pet_id': 'id',
               'pet_name': 'name',
               'pet_type': 'type'
           }
       }
   }
   ```

### Phase 2: Migration Implementation
```python
class DataMigrator:
    async def migrate_table(
        self,
        source_table: str,
        batch_size: int = 1000
    ):
        mapping = MIGRATION_MAPPINGS[source_table]
        
        # Get total records
        total = await self.db.fetch_val(
            f"SELECT COUNT(*) FROM {source_table}"
        )
        
        # Migrate in batches
        for offset in range(0, total, batch_size):
            records = await self.db.fetch_all(
                f"SELECT * FROM {source_table} "
                f"LIMIT {batch_size} OFFSET {offset}"
            )
            
            transformed = [
                self._transform_record(r, mapping['field_mappings'])
                for r in records
            ]
            
            await self.db.execute_many(
                f"INSERT INTO {mapping['target_table']} "
                f"({','.join(mapping['field_mappings'].values())}) "
                f"VALUES ({','.join(['?'] * len(mapping['field_mappings']))})",
                transformed
            )
```

## 4. Frontend Development and Integration

### Architecture
```
frontend/
├── src/
│   ├── api/
│   │   ├── taskApi.ts    # Task management API
│   │   ├── petsApi.ts    # Battle pets API
│   │   └── plexApi.ts    # Plex integration API
│   ├── components/
│   │   ├── TaskList/
│   │   ├── PetBattle/
│   │   └── MediaPlayer/
│   └── stores/
│       ├── taskStore.ts
│       └── petStore.ts
```

### API Integration
```typescript
// src/api/taskApi.ts
export class TaskApi {
    async getTasks(): Promise<Task[]> {
        const response = await fetch('/api/v1/tasks', {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        return response.json();
    }

    async createTask(task: TaskCreate): Promise<Task> {
        const response = await fetch('/api/v1/tasks', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(task)
        });
        return response.json();
    }
}
```

### State Management
```typescript
// src/stores/taskStore.ts
import create from 'zustand';
import { TaskApi } from '../api/taskApi';

interface TaskStore {
    tasks: Task[];
    loading: boolean;
    error: Error | null;
    fetchTasks: () => Promise<void>;
    createTask: (task: TaskCreate) => Promise<void>;
}

export const useTaskStore = create<TaskStore>((set) => ({
    tasks: [],
    loading: false,
    error: null,
    fetchTasks: async () => {
        set({ loading: true });
        try {
            const api = new TaskApi();
            const tasks = await api.getTasks();
            set({ tasks, loading: false });
        } catch (error) {
            set({ error, loading: false });
        }
    },
    createTask: async (task) => {
        set({ loading: true });
        try {
            const api = new TaskApi();
            const newTask = await api.createTask(task);
            set(state => ({
                tasks: [...state.tasks, newTask],
                loading: false
            }));
        } catch (error) {
            set({ error, loading: false });
        }
    }
}));
```

## 5. Battle Pets Resolution

### Integration with Task System
```python
class BattlePetRewardSystem:
    def __init__(self, task_service: TaskService, pet_service: PetService):
        self.task_service = task_service
        self.pet_service = pet_service

    async def process_task_completion(
        self,
        task_id: int,
        user_id: int
    ):
        task = await self.task_service.get_task(task_id)
        if task.status == TaskStatus.COMPLETED:
            pet = await self.pet_service.get_user_active_pet(user_id)
            if pet:
                # Award experience based on task difficulty
                exp_gain = self._calculate_exp_gain(task)
                await self.pet_service.award_experience(
                    pet_id=pet.id,
                    experience=exp_gain
                )
```

### Master.py Resolution
The functionality in `master.py` will be:
1. Migrated to proper service structure
2. Integrated with task completion rewards
3. Made available through API endpoints
4. Connected to Discord commands

### New Structure:
```
src/
├── pets/
│   ├── models.py      # Pet data models
│   ├── service.py     # Pet service implementation
│   ├── rewards.py     # Reward calculation
│   └── battle.py      # Battle mechanics
└── tasks/
    ├── models.py      # Task data models
    ├── service.py     # Task service implementation
    └── rewards.py     # Task reward integration
```

## Updated Timeline

The implementation of these components requires adjusting our timeline:

1. Days 1-10: Development Foundation (unchanged)
2. Days 11-20: Application Core (unchanged)
3. Days 21-35: Feature Implementation
   - Days 21-25: Discord & Plex Integration
   - Days 26-30: Battle Pets Migration & Integration
   - Days 31-35: Frontend Development
4. Days 36-45: Monitoring & Operations
5. Days 46-50: Production Readiness

Total: 50 days (additional 5 days for proper integration)