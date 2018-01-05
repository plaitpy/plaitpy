PYTHON_BIN="python"


function run_yaml() {
  ${PYTHON_BIN} main.py ${1} --num 10 --csv > /dev/null 2>&1
  if (( $? == 0 )); then
    echo "PASS: ${1}"
  else
    echo "${1} FAILED WITH ${?}!"
    ${PYTHON_BIN} main.py ${1} --num 10 --csv > /dev/null
    exit 1
  fi

}

for f in `find ./templates/ -type f -regex ".*\.y.?ml"`; do
  run_yaml "${f}"
done
