# repeatedly run pytest
# trigger a new run whenever a .py file changes,
# abort the loop if a test case fails
#    (and the suite has been passed before)

PASSED=""

while :
do
    if py.test
    then
	PASSED=1
    else
	[ $PASSED ] && exit
    fi
    inotifywait $(find . -name "*.py") -e modify -e close_write
    sleep 1
done
