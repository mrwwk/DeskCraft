bash start_evocua_interactive.sh

if [ $? -eq 0 ]; then
    echo "start_evocua_interactive.sh completed successfully, starting start_evocua_interactive_backup.sh"
    bash start_evocua_interactive_backup.sh
else
    echo "start_evocua_interactive.sh failed with exit code $?"
    exit 1
fi
