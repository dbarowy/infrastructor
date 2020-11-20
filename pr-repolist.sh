repos=($(ls -d PATHGLOB))
for repo in ${repos[*]}; do
    python pull-request.py USERNAME PASSWORD $repo config.WHATEVER.json
done


