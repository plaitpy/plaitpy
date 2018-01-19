[ -z "${PYTHON_BIN}" ] && PYTHON_BIN="python"
echo "TESTING WITH ${PYTHON_BIN}"

function run_yaml() {
  ${PYTHON_BIN} main.py ${1} --num 10 --csv --exit-on-error > /dev/null 2>&1
  if (( $? == 0 )); then
    echo "PASS: ${1}"
  else
    echo "${1} FAILED WITH ${?}!"
    ${PYTHON_BIN} main.py ${1} --num 10 --csv --exit-on-error > /dev/null
    exit 1
  fi

}

for f in `find ./templates/ -type f -regex ".*\.y.?ml"`; do
  run_yaml "${f}"
done
