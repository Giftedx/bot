# Media Server with Adaptive Streaming and Management

[![Build Status](https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>/actions/workflows/main.yml/badge.svg)](https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>/actions/workflows/main.yml) [![codecov](https://codecov.io/gh/<YOUR_USERNAME>/<YOUR_REPOSITORY>/branch/main/graph/badge.svg)](https://codecov.io/gh/<YOUR_USERNAME>/<YOUR_REPOSITORY>) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Introduction

This project is a robust and scalable media server built using Python, designed for streaming and managing media content.  It leverages modern technologies like FFmpeg, Redis, asyncio, and Discord integration to provide a high-performance and feature-rich experience. The server supports adaptive bitrate streaming, background task processing, health checks, comprehensive metrics, and secure operation.  It includes both a REST API for general management and a Discord bot interface for convenient user interaction. 


## Features

*   **Adaptive Bitrate Streaming:** Dynamically adjusts video bitrate based on network conditions using a PID controller for optimal viewing experience.
*   **FFmpeg Integration:** Utilizes FFmpeg for efficient media transcoding and streaming.
*   **Redis Integration:** Leverages Redis for task queuing, caching, and real-time data, providing high performance and scalability.
*   **Asynchronous Architecture:**  Built with asyncio for non-blocking I/O operations, allowing for high concurrency.
*   **Discord Bot Integration:**  Allows users to interact with the media server directly through Discord commands.
*   **REST API:** Provides a RESTful API for managing the server and interacting with media.
*   **Backpressure Handling:**  Implements a robust backpressure system using token bucket rate limiting and load shedding to maintain server stability under heavy load.
*   **Comprehensive Monitoring:** Includes extensive metrics using Prometheus and visualizes data using dashboards.(grafana suggested)
*   **Health Checks:** Provides health check endpoints for monitoring server status.
*   **Dependency Injection:** Uses dependency injection for clean architecture and testability.
*   **Configuration Management:** Uses a structured settings management system for easy configuration.
*   **Error Handling:** Implements robust error handling and custom exception classes.
*   **Input Validation:** Uses Pydantic and `bleach` to validate and sanitize all user inputs to prevent security vulnerabilities (command injection, XSS, path traversal).
*   **Dockerized Deployment:** Includes Dockerfile and docker-compose for easy deployment.
*   **Kubernetes deployment**: Added files to prepare K8s deployment
*   **Process Management:** Uses psutil for cross-platform process monitoring and management.
*   **Testing:** Well documented, multi-level test. (unit, integration...). With Shell script, and playwright usage.
*   **Background Shutdown:** Proper shutdown logic to clean processes in the background, improving security and reducing zombie processes creation.
*   **Adaptive streaming quality:** Aims to provide real time smooth stream quality adjustment.
*   **UI components**: Several clear UI components and static resources provided, improving the application overview, dashboards and configurations.
    *   activity heatmap.
    *   media widgets.
    *   network flow diagram
    *   notification center
    *   settings panel

UPDATED PROJECT STRUCTURE HERE
```
Structural changes have been made to improve project organization.
Please refer to the file listing below for the updated structure.
.
UPDATED PROJECT STRUCTURE HERE
├── Dockerfile                     # Docker build file.
├── docker-compose.yml             # Docker Compose configuration.

├── requirements.txt               # Dependencies
├── README.md                      # This file.
├── requirements-dev.txt           # Dependencies only needed by developers.
├── security/                      # Security-related configurations/scripts.
.
│   └── SECURITY.md                # Security documentation
├── scripts/                       # Useful scripts and development scripts
├── src/                           # Source code directory.
├── adaptive_quality_test_plan.md  # Testing documentation.
│   ├── bot/                       # Discord bot integration.
│   ├── api/                       # REST API endpoints.
│   │   ├── discord_bot.py         # Discord bot implementation
│   └── dev_scripts/             # Development scripts (move_files.bat, mkdirs.bat)
│   │   ├── discord_selfbot.py     # Discord selfbot implementation
│   │   ├── health.py              # Health check endpoints.
│   ├── config/                    # Configuration files.
│   │   ├── selfbot.py             # Selfbot implementation
│   │   └── config/              # Configuration settings
├── Dockerfile # Docker build file.
│   │       └── secrets.py         # Secrets management
│   │   └── cogs/                 # Discord bot cogs (command modules).
│   │   ├── caching.py             # Shared caching functionalities.
│   ├── core/                      # Core application logic and utilities.
│   │   ├── circuit_breaker.py     # Circuit breaker implementation for resilience
│   │   └── routes.py              # API route definitions.
│   │   ├── di_container.py        # Dependency injection container
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── notification_manager.py# Notifications features.
│   │   ├── enums.py               # Possible enums definition
│   │   ├── plex_manager.py        # Plex specific related features.
│   │       └── media_commands.py  # Media-related commands cog.
│   │   ├── queue_manager.py       # Task queuing using Redis.
│   │   ├── ffmpeg_manager.py      # Manages FFmpeg processes and configurations
│   │   ├── settings_validator.py  # Settings validation.
│   │   ├── rate_limiter.py        # Rate limiting utility
│   │   ├── service_clients.py     # Generic service client definitions.
│   │   ├── backpressure.py        # Adaptive controller/ Token Bucket/ Rejection Strategy ...
│   │   └── tautulli_client.py     # Interaction with Tautulli.
│   │   ├── redis_manager.py       # Wrapper to add async access to redis storage.
│   ├── monitoring/                # Monitoring and metrics related modules
│   │   └── user_preferences.py    # User preferences storage and handling.
│   │   └── metrics.py             # Application metrics definition
│   │   ├── media_player.py
│   ├── ui/                        # User interface components and resources.
│   ├── media/                     # Media processing related modules
│   │   │   ├── media_browser.py   # Media browser UI component.
│   │   ├── components/            # UI components
│   │   │   ├── media_queue.py     # Media queue UI component.
│   │   ├── settings_manager.py    # Manages application settings.
│   │   │   ├── network_flow.py    # Network flow diagram UI component.
│   │   │   ├── activity_heatmap.py# Activity heatmap component.
│   │   │   │   ├── custom.css
│   │   │   └── search_interface.py# Search interface UI component.
│   │   │   │   ├── main.css
│   │   └── processor.py           # Media processor implementation
│   │   │   │   └── styles.css
│   │   ├── static/                # Static resources for the web application
│   │       ├── error.html
│   │   │   └── js/                # JavaScript files
│   │       └── index.html
│   │   │   ├── base_widget.py     # Base UI widget class.
│   ├── utils/                     # General utility functions and helpers
│   │   └── templates/           # HTML templates
│   │   ├── rate_limiter.py        # Rate limiting utilities
│   │   ├── logging_setup.py       # Centralized logging setup.
│   │   └── redis_manager.py       # Redis utilities
│   │   │   ├── css/               # CSS stylesheets
│   └── server_main.py             # Main entry point for the media server application
│   │   ├── performance.py         # Performance measurement tools.
    ├── playwright/                # Playwright tests suite
├── test_scripts/                  # Test scripts
    └── ...                        # Other test files
│   │       ├── base.html
```
│   └── run_tests.sh               # Test runner script
│   │   ├── plex.py                # Plex utilities
└── tests/                         # Test suites.
├── README.md # This file.
├── adaptive_quality_test_plan.md # Testing documentation.
├── docker-compose.yml # Docker Compose configuration.
├── requirements.txt # Dependencies
├── requirements-dev.txt # Dependencies only needed by developpers.
├── scripts/ # Useful scripts (shutdown...)
├── security/ # Security-related configurations/scripts.
├── src/ # Source code directory.
│ ├── api/ # REST API endpoints.
│ │ ├── health.py # Health check endpoints.
│ │ └── routes.py # API route definitions.
│ ├── bot/ # Discord bot integration.
│ │ └── discord_bot.py # discord selfbot implementation
│ │ └── main.py # main entry point for the discord Bot part
│ ├── cogs/ # Discord bot cogs (command modules).
│ │ └── media_commands.py # Media-related commands cog.
│ ├── core/ # Core application logic and utilities.
│ │ ├── exceptions.py # custom exceptions
│ │ ├── backpressure.py # Adaptive controller/ Token Bucket/ Rejection Strategy ...
│ │ ├── caching.py # Shared caching functionalities.
│ │ ├── circuit_breaker.py # Circuit breaker implementation for resilience
│ │ ├── di_container.py # Dependency injection container
│ │ ├── enums.py # Possible enums definition
│ │ ├── ffmpeg_manager.py # Manages FFmpeg processes and configurations
│ │ ├── media_player.py
│ │ ├── notification_manager.py # Notifications features.
│ │ ├── plex_manager.py # Plex specific related features.
│ │ ├── queue_manager.py # Task queuing using Redis.
│ │ ├── rate_limiter.py # Rate limiting utility
│ │ ├── redis_manager.py # Wrapper to add async access to redis storage.
│ │ ├── settings_manager.py # Central settings management system
│ │ ├── settings_validator.py # Settings validation.
│ │ ├── service_clients.py # generic service client definitions.
│ │ └── tautulli_client.py # Interaction with Tautulli.
│ │ └── user_preferences.py # User preferences storage and handling.
│ ├── media/ # media
│ │ └── processor.py # Placeholder name; likely for pre/post-processing tasks
│ ├── monitoring/
│ ├── alerts.py # define the alerting
│ └── metrics.py # Application metrics definition
│ ├── security/ # Security helpers.
│ │ └── input_validation.py # Input sanitization and validation.
│ ├── ui/ # structure for user interface components.
│ │ └── components
│ │ └── activity_heatmap.py # Activity heatmap.
│ │ └── base_widget.py # UI base widget.
│ │ └── media_browser.py # UI
│ │ └── media_queue.py # UI
│ │ └── network_flow.py # network flow display.
│ │ └── search_interface.py # UI for searching feature.
│ │ └── static # contains the statics resources for the web application
│ │ └── css # StyleSheet files.
│ │ └── custom.css
│ │ └── main.css
│ │ └── styles.css
│ │ └── js # JavaScript code and resources
│ │ └── templates # contains website html template files
│ │ └── base.html
│ │ └── error.html
│ │ └── index.html
│ │ └── widgets # Widgets UI elements
│ │ └── activity_feed.py
│ │ └── activity_heatmap.py # Specific display logic
│ │ └── media_browser.py # browsing elements
│ │ └── media_player.py # UI for player features
│ │ └── network_flow.py # network activity
│ │ └── notification_center.py # UI element related to notifications
│ │ └── settings_panel.py # Panel logic to edit setting
│ │ └── search_interface.py # Specific for the search bar
│ │
│ ├── utils/ # General utility functions and helpers
│ │ └── logging_setup.py # Centralized logging setup for the application.
│ │ └── performance.py # Tools related to performances like measure_latency decorator
│ │ └── plex.py # Plex utility functions
│ │ └── rate_limiter.py # Rate limiting utilities
│ │ └── redis_manager.py # Redis utilities
│ └── discord_selfbot.py
├── test_scripts #test script used
│ └── run_tests.sh #test runner, used to launch integration, and playwright test
└── tests #test suites.
├── playwright #playwright tests suite
├── test_activity_feed.py #Test suites to check Activity Feed.
├── test_activity_heatmap.py #
├── test_alerts.py #Test for alerts.
├── test_backpressure.py #backpressure logic testing
├── test_caching.py #
├── test_circuit_breaker.py #
├── test_config.py #validation/ loading.
├── test_dashboard.py #
├── test_dependencies.py #
├── test_di_container.py #Test
├── test_discord_bot.py #Discord related tests
├── test_exceptions.py # Custom exception handling tests.
├── test_ffmpeg_manager.py # testing for ffmpeg command generation, and execution monitoring
├── test_health.py #Healthcheck endpoints testing.
├── test_input_validation.py # Test for security measures around user input validation
├── test_logging_setup.py # Check for log functionalities, levels, and format
├── test_main.py #testing app initialization and shutdown events
├── test_media_browser.py #Tests the functionalities to display and browse.
├── test_media_commands.py # Testing the core media playing features.
├── test_media_player.py #media player functionalities and its control logic
├── test_media_queue.py # media Queue verification, to test interactions such as adding or removing elements.
├── test_metrics.py # test metrcis monitoring
├── test_network_flow.py # Testing UI displaying network diagram data.
├── test_notification_center.py # Tests for UI widget related to the Notification System
├── test_notification_manager.py # Notifications
├── test_performance.py # Tests related to performance measurement, like decorator
├── test_plex_manager.py #Plex integration related testing.
├── test_plex.py # test the Plex utilities, like server interaction
├── test_processor.py # Test related to FFmpeg transcoding
├── test_prometheus_alerts.py #Test prometheus related functionalities
├── test_queue_manager.py #Redis queue
├── test_rate_limiter.py #Test ratelimiter decorator logic.
├── test_redis_manager.py # Tests covering the Redis management features.
├── test_routes.py # Tests associated to route definition and routing logic.
├── test_scripts.py # Scripts testing
├── test_search_interface.py #
├── test_secrets.py #Check how secrets are treated by the project
├── test_selfbot.py # Ensure that a selfbot implementation work fine.
├── test_service_clients.py # Ensure good interaction of the application and the used clients
├── test_settings_manager.py #Check setting management is OK (read write values...)
├── test_settings_panel.py # Check if the Settings UI works.
├── test_settings_validator.py #Validate that configuration data verification steps
├── test_tautulli_client.py # Tests focused on communication between app and the Tautulli services
└── test_user_preferences.py # Test to manage User preferences

## Setup and Installation

This section provides instructions on setting up the development environment, installing dependencies, and running the application.

### Prerequisites

*   Python 3.8+
*   FFmpeg (installed and available in your system's PATH)
*   Redis
*   pip
*   Poetry (recommended for dependency management)

### Installation
1:  Clone repo
    ```
   git clone <YOUR_REPOSITORY_URL>
    cd <YOUR_REPOSITORY_NAME>

    ```
2.  **Install Dependencies (using Poetry):**

    ```bash
    poetry install
    ```
    If you don't have Poetry, you can install it with:
    ```bash
       curl -sSL https://install.python-poetry.org | python3 -
    ```
    Alternatively install using `pip`:
       ```
       pip install -r requirements.txt
        ```

### Configuration
Configuration is now centrally managed through the `settings_manager.py` module in the core directory. Settings can be loaded from:
- Environment variables
- .env files
- Command line arguments

The application uses a hierarchical settings system with validation via Pydantic models.

    Create a .env file in the root directory of the project and populate with the correct values like provided
    inside the `.env.exemple`

*   **`FFMPEG_PATH`:**  (Optional) Path to your FFmpeg executable. If not set, the system PATH is used.
*   **`REDIS_HOST`:** Redis server hostname. (Default: `localhost`)
*  **`REDIS_PORT`:** Redis server port. (Default: `6379`)
*  **`REDIS_DB`**: Redis database number.(Default: 0)
* **`PLEX_URL`**: Your Plex server URL
* **`PLEX_TOKEN`**: Your Plex authentication Token.
*   **`DISCORD_TOKEN`:**  (Optional) Your Discord bot token.
* **`TAUTULLI_URL`:** (Optional) Url to your Tautulli instance.
*   **`TAUTULLI_API_KEY`:** Tautulli API Key.
*   And others settings shown inside the `.env.example`

    You may adjust these values, using a `.env` file, environment variables. 

## Running the Application
    ```
     poetry run python src/main.py

    ```

    The application should now be running, and you can access the web interface (usually at http://localhost:8080, but may depend on configuration. Look for access_url in your logs).  The Discord bot (if configured) will connect.


    ## Testing
    Tests are separated in two groups, `unit` test, and `integration` test.
    
    Use the test script
    ```
    test_scripts/run_tests.sh

    ```

## API Reference
A dedicated API specification is recommended and can be found within `/docs/api_specification.md`. Or it could be generated dynamically at `/docs`, in that second case this is an example

GET /api/health

Returns the health status of the server and its dependencies (Redis, FFmpeg).

*    Success Response:
    *    Code: 200 OK
    *    Content:
    ```
     {
          "status": "OK",
          "dependencies": {
             "redis": "OK",
             "ffmpeg": "OK"
          }
     }

    ```
     *  Error responses are returned if healtcheck detected problem.


GET /api/queue

Returns queue elements

*    Success Response:
    *    Code: 200 OK
    *    Content:

        ```
        {
          "queue": [
            {
              "item": "item1",
              ...
            }
         ],

        }
        ```


## Contributing

Contributions are welcome! Please follow these guidelines:
...
## License
This Project is licensed under MIT License.