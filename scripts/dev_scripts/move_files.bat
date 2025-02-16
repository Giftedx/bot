@echo off

IF EXIST src\application.py move src\application.py src\server\application.py 2>nul
IF EXIST src\bot.py move src\bot.py src\server\bot.py 2>nul
IF EXIST src\dependencies.py move src\dependencies.py src\server\dependencies.py 2>nul
IF EXIST src\discord_bot.py move src\discord_bot.py src\server\bot\discord_bot.py 2>nul
IF EXIST src\discord_selfbot.py move src\discord_selfbot.py src\server\bot\discord_selfbot.py 2>nul
IF EXIST src\healthcheck.py move src\healthcheck.py src\server\api\healthcheck.py 2>nul
IF EXIST src\main.py move src\main.py src\server\main.py 2>nul
IF EXIST src\metrics.py move src\metrics.py src\server\monitoring\metrics.py 2>nul
IF EXIST src\plex_server.py move src\plex_server.py src\server\services\plex_server.py 2>nul
IF EXIST src\selfbot.py move src\selfbot.py src\server\bot\selfbot.py 2>nul
IF EXIST src\api move src\api src\server\api 2>nul
IF EXIST src\cogs move src\cogs src\server\bot\cogs 2>nul
IF EXIST src\config move src\config src\server\config 2>nul
IF EXIST src\core move src\core src\server\core 2>nul
IF EXIST src\monitoring move src\monitoring src\server\monitoring 2>nul
IF EXIST src\security move src\security src\server\security 2>nul
IF EXIST src\services move src\services src\server\services 2>nul
IF EXIST src\utils move src\utils src\server\utils 2>nul
IF EXIST ui\dashboard.py move ui\dashboard.py src\client\ui\dashboard.py 2>nul
IF EXIST ui\themes.py move ui\themes.py src\client\ui\themes.py src\client\ui\themes.py 2>nul
IF EXIST ui\components move ui\components src\client\ui\components 2>nul
IF EXIST ui\static move ui\static src\client\ui\static 2>nul
IF EXIST ui\templates move ui\templates src\client\ui\templates 2>nul
IF EXIST ui\widgets move ui\widgets src\client\ui\widgets 2>nul
IF EXIST test_scripts move test_scripts tests\test_scripts 2>nul
IF EXIST tests\playwright move tests\playwright tests\playwright 2>nul
IF EXIST tests move tests tests\unit 2>nul
IF EXIST src\ui\dashboard.py move src\ui\dashboard.py src\client\ui\dashboard.py 2>nul
IF EXIST src\ui\themes.py move src\ui\themes.py src\client\ui\themes.py 2>nul

echo Files and directories moved (or not found)