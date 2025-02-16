# Create necessary directories if they don't exist
$directories = @(
    "src\core\game",
    "src\core\pets",
    "src\core\utils",
    "src\database\schema"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created directory: $dir"
    }
}

# Move battle_system.py to game directory
Write-Host "`nMoving battle system files..."
if (Test-Path "src\core\utils\battle_system.py") {
    if (-not (Test-Path "src\core\game")) {
        New-Item -ItemType Directory -Force -Path "src\core\game" | Out-Null
    }
    Move-Item "src\core\utils\battle_system.py" "src\core\game\battle_system.py" -Force
    Write-Host "Moved battle_system.py to game directory"
}

# Clean up empty or corrupt files
Write-Host "`nCleaning up potentially corrupt files..."
Get-ChildItem -Path "src" -Recurse -File | Where-Object { $_.Length -lt 10 } | ForEach-Object {
    Write-Host "Found small file: $($_.FullName) (Size: $($_.Length) bytes)"
    if ($_.Length -eq 0 -or $_.Length -eq 1) {
        Remove-Item $_.FullName
        Write-Host "Removed empty/corrupt file: $($_.FullName)"
    }
}

# Clean up directory-named files
Write-Host "`nCleaning up directory-named files..."
Get-ChildItem -Path "src" -Recurse -File | Where-Object { 
    $parentDir = Split-Path -Leaf (Split-Path -Parent $_.FullName)
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
    $parentDir -eq $fileName
} | ForEach-Object {
    Write-Host "Found directory-named file: $($_.FullName)"
    Remove-Item $_.FullName
    Write-Host "Removed directory-named file: $($_.FullName)"
}

# Verify final structure with detailed info
Write-Host "`nVerifying final structure..."
$verifyDirs = @(
    "src\core\game",
    "src\core\pets",
    "src\core\utils",
    "src\database",
    "src\cogs\pokemon",
    "src\cogs\osrs",
    "src\cogs\media"
)

foreach ($dir in $verifyDirs) {
    Write-Host "`nFiles in directory: $dir"
    if (Test-Path $dir) {
        $files = Get-ChildItem -Path $dir -File
        if ($files) {
            $files | ForEach-Object {
                $content = if ($_.Length -gt 0) { "OK" } else { "EMPTY!" }
                Write-Host "  - $($_.Name) (Size: $($_.Length) bytes, Status: $content)"
            }
        } else {
            Write-Host "  (empty)"
        }
    } else {
        Write-Host "  (directory not found)"
    }
}

Write-Host "`nFinal cleanup complete!" 