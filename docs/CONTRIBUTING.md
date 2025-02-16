# Contributing to Discord Plex Player

First off, thank you for considering contributing to Discord Plex Player! It's people like you that make Discord Plex Player such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

#### Before Submitting A Bug Report

* Check the [documentation](docs/) for a list of common questions and problems.
* Check if the issue has already been reported in our [issue tracker](https://github.com/yourusername/discord-plex-player/issues).
* Perform a cursory search to see if the problem has already been reported.

#### How Do I Submit A (Good) Bug Report?

Bugs are tracked as GitHub issues. Create an issue and provide the following information:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots and animated GIFs if possible
* Include your environment details:
  - OS version
  - Python version
  - Discord.py version
  - Plex server version
  - Redis version

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

#### Before Submitting An Enhancement Suggestion

* Check the [documentation](docs/) to see if the feature is already supported.
* Check if the enhancement has already been suggested in our [issue tracker](https://github.com/yourusername/discord-plex-player/issues).

#### How Do I Submit A (Good) Enhancement Suggestion?

Enhancement suggestions are tracked as GitHub issues. Create an issue and provide the following information:

* Use a clear and descriptive title
* Provide a detailed description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other applications where this enhancement exists, if applicable
* Include screenshots and animated GIFs if possible

### Pull Requests

#### Setting Up the Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/discord-plex-player.git
   cd discord-plex-player
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

#### Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes:
   * Follow the [code style guide](#code-style-guide)
   * Write [good commit messages](#commit-messages)
   * Keep your changes focused and atomic

3. Test your changes:
   ```bash
   pytest
   flake8
   black .
   mypy .
   ```

4. Update documentation if needed

#### Submitting Changes

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Submit a pull request:
   * Use a clear and descriptive title
   * Include all relevant information in the description
   * Link any related issues
   * Update documentation if needed

## Code Style Guide

### Python Code Style

1. Follow PEP 8
2. Use type hints
3. Write docstrings (Google style)
4. Keep functions focused and small
5. Use meaningful variable names

Example:
```python
from typing import List, Optional

def process_media(media_id: str) -> Optional[dict]:
    """
    Process media and return its information.

    Args:
        media_id: The unique identifier of the media.

    Returns:
        dict: Media information or None if not found.

    Raises:
        MediaNotFoundError: If media_id is invalid.
    """
    try:
        return fetch_media_info(media_id)
    except MediaNotFoundError:
        logger.error(f"Media not found: {media_id}")
        return None
```

### JavaScript Code Style

1. Use ES6+ features
2. Use async/await
3. Follow ESLint configuration
4. Write JSDoc comments

Example:
```javascript
/**
 * Fetch media information from the API.
 * @param {string} mediaId - The media identifier.
 * @returns {Promise<Object>} Media information.
 */
async function fetchMediaInfo(mediaId) {
    try {
        const response = await api.get(`/media/${mediaId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch media:', error);
        throw error;
    }
}
```

## Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 🚱 `:non-potable_water:` when plugging memory leaks
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * 💚 `:green_heart:` when fixing the CI build
    * ✅ `:white_check_mark:` when adding tests
    * 🔒 `:lock:` when dealing with security
    * ⬆️ `:arrow_up:` when upgrading dependencies
    * ⬇️ `:arrow_down:` when downgrading dependencies

Example:
```
🎨 Improve structure of media processing module

- Split media processing into smaller functions
- Add type hints
- Improve error handling
- Update documentation

Fixes #123
```

## Testing

### Writing Tests

1. Write unit tests for new features
2. Update existing tests when modifying features
3. Include integration tests when needed
4. Aim for high test coverage

Example:
```python
def test_media_processing():
    # Arrange
    media_id = "test_123"
    expected_title = "Test Media"
    
    # Act
    result = process_media(media_id)
    
    # Assert
    assert result is not None
    assert result["title"] == expected_title
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_media.py

# Run with coverage
pytest --cov=src tests/
```

## Documentation

### Writing Documentation

1. Update README.md if needed
2. Update API documentation
3. Add examples for new features
4. Include docstrings in code

Example:
```markdown
## Media Processing

The `process_media` function handles media information retrieval:

```python
result = process_media("media_123")
print(result["title"])
```

### Generating Documentation

```bash
# Generate API documentation
sphinx-build -b html docs/source docs/build
```

## Review Process

1. All code changes require review
2. Reviewers will look for:
   * Correct functionality
   * Code style
   * Test coverage
   * Documentation
   * Performance impact
   * Security considerations

## Community

* Join our [Discord server](https://discord.gg/your-invite)
* Follow our [Twitter](https://twitter.com/your-twitter)
* Read our [blog](https://your-blog.com)

## Questions?

* Check our [FAQ](docs/faq.md)
* Ask in our Discord server
* Create a [GitHub Discussion](https://github.com/yourusername/discord-plex-player/discussions)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
