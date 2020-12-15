# https://github.com/jazzband/pip-tools/issues/625

PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if [[ -z "$PYTHON_VERSION" ]]; then
    echo -e "\e[31;1mERROR: environment variable PYTHON_VERSION needs to be defined!\e[0m"
    exit 1
fi

mkdir -p dev/$PYTHON_VERSION &&
    python dev/extract_install_requires.py &&
    cp dev/requirements*.in dev/$PYTHON_VERSION/ &&
    rm dev/$PYTHON_VERSION/requirements-dev.in &&
    pip-compile --upgrade \
        dev/requirements*.in \
        -o dev/$PYTHON_VERSION/requirements-dev.txt &&
    for in_file in $(ls dev/$PYTHON_VERSION/requirements*.in); do
        echo -e "-c requirements-dev.txt\n$(cat ${in_file})" >${in_file}
        pip-compile "${in_file}"
    done &&
    pip-sync dev/$PYTHON_VERSION/requirements*.txt &&
    exit 0

exit 1 # if failure
