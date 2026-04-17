bash start_all.sh

if [ $? -eq 0 ]; then
    echo "start_all.sh completed successfully, starting start_evocua_interactive.sh"
    bash start_evocua_interactive.sh
else
    echo "start_all.sh failed with exit code $?"
    exit 1
fi
