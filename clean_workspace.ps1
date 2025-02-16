# Create new clean workspace directory
$cleanDir = "clean_bot"
Remove-Item -Path $cleanDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $cleanDir
New-Item -ItemType Directory -Force -Path "$cleanDir/src"
New-Item -ItemType Directory -Force -Path "$cleanDir/src/core"
New-Item -ItemType Directory -Force -Path "$cleanDir/src/core/app"
New-Item -ItemType Directory -Force -Path "$cleanDir/src/plex"
New-Item -ItemType Directory -Force -Path "$cleanDir/src/bot"

# Copy only the essential files
Copy-Item "src/main.py" "$cleanDir/src/"
Copy-Item "src/bot.py" "$cleanDir/src/"
Copy-Item "src/core/config.py" "$cleanDir/src/core/" -ErrorAction SilentlyContinue
Copy-Item "src/core/app/bot.py" "$cleanDir/src/core/app/" -ErrorAction SilentlyContinue
Copy-Item "src/plex/bot.py" "$cleanDir/src/plex/" -ErrorAction SilentlyContinue
Copy-Item "src/bot/plex_selfbot.py" "$cleanDir/src/bot/" -ErrorAction SilentlyContinue

# Create minimal .cursorignore
@"
# Only allow these specific files
*
!/src/main.py
!/src/bot.py
!/src/core/config.py
!/src/core/app/bot.py
!/src/plex/bot.py
!/src/bot/plex_selfbot.py
"@ | Out-File "$cleanDir/.cursorignore" -Encoding UTF8

# Copy essential config
Copy-Item ".env" "$cleanDir/" -ErrorAction SilentlyContinue

Write-Host "Clean workspace created in ./$cleanDir"
Write-Host "Open this directory in Cursor to test with minimal files." 