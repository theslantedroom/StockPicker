@ECHO OFF
ECHO Make something
git status
git add -A
git rm --cached finance.db
git status
git commit -m "push update"
git push


