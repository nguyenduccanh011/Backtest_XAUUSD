# PowerShell script to commit changes
git add gui.py
git add src/config/strategy_config.py
git add .gitattributes
git add manifest.yml

git commit -m "refactor(gui): remove DictConfigWrapper duplication, use StrategyConfig" `
           -m "- Refactor StrategyConfig to support config_dict parameter" `
           -m "- Replace DictConfigWrapper with StrategyConfig in gui.py" `
           -m "- Add .gitattributes to manage line endings (LF for text files)" `
           -m "- Update manifest.yml to track .gitattributes"

Write-Host "✅ Commit completed!" -ForegroundColor Green
git log --oneline -1

