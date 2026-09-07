#!/usr/bin/env bash
# BlackSharkCars one-shot runner (macOS / Linux)
# Usage: ./run.sh           -> asks Docker or local
#        ./run.sh docker    -> Docker mode
#        ./run.sh local     -> local mode
#        ./run.sh tests     -> run tests only

set -e
cd "$(dirname "$0")"

if [ "$1" = "docker" ]; then
    python3 run.py --docker
elif [ "$1" = "local" ]; then
    python3 run.py --local
elif [ "$1" = "tests" ]; then
    python3 run.py --tests
else
    python3 run.py
fi