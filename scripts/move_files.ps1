# Create necessary directories
New-Item -ItemType Directory -Force -Path "src\core\game", "src\core\pets", "src\database\schema", "src\core\utils"

# Function to safely move files
function Move-FileIfExists {
    param (
        [string]$sourcePath,
        [string]$destPath
    )
    
    if (Test-Path $sourcePath) {
        $destDir = Split-Path -Parent $destPath
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        Move-Item -Path $sourcePath -Destination $destPath -Force
        Write-Host "Moved $sourcePath to $destPath"
    }
}

# Move core files
Move-FileIfExists "cogs\game_math.py" "src\core\game\math.py"
Move-FileIfExists "cogs\battle_system.py" "src\core\game\battle.py"
Move-FileIfExists "cogs\pet_core.py" "src\core\pets\core.py"
Move-FileIfExists "cogs\pet_manager.py" "src\core\pets\manager.py"

# Move database files
Move-FileIfExists "cogs\database.py" "src\database\db.py"
Move-FileIfExists "cogs\models.py" "src\database\models.py"
Move-FileIfExists "cogs\osrs_schema.sql" "src\database\schema\osrs.sql"

# Move utility files
Move-FileIfExists "cogs\activities.py" "src\core\utils\activities.py"
Move-FileIfExists "cogs\admin.py" "src\core\utils\admin.py"
Move-FileIfExists "cogs\combat.py" "src\core\utils\combat.py"
Move-FileIfExists "cogs\fun.py" "src\core\utils\fun.py"
Move-FileIfExists "cogs\games.py" "src\core\utils\games.py"
Move-FileIfExists "cogs\gathering.py" "src\core\utils\gathering.py"
Move-FileIfExists "cogs\voice.py" "src\core\utils\voice.py"
Move-FileIfExists "cogs\world_manager.py" "src\core\utils\world_manager.py"

# Compare and merge command files
$commandFiles = Get-ChildItem -Path "cogs" -Filter "*_commands.py"
foreach ($file in $commandFiles) {
    $srcFile = "src\cogs\$($file.Name)"
    if (Test-Path $srcFile) {
        # File exists in both places - keep newer version
        $srcDate = (Get-Item $srcFile).LastWriteTime
        $cogDate = $file.LastWriteTime
        if ($cogDate -gt $srcDate) {
            Move-Item -Path $file.FullName -Destination $srcFile -Force
            Write-Host "Updated $($file.Name) with newer version"
        } else {
            Write-Host "Kept existing version of $($file.Name)"
        }
    } else {
        # File only exists in cogs - move it
        Move-Item -Path $file.FullName -Destination $srcFile
        Write-Host "Moved $($file.Name) to src\cogs"
    }
}

Write-Host "File reorganization complete" 