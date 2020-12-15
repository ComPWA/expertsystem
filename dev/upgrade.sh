PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if [[ -z "$PYTHON_VERSION" ]]; then
    echo -e "\e[31;1mERROR: environment variable PYTHON_VERSION needs to be defined!\e[0m"
    exit 1
fi

mkdir -p dev/$PYTHON_VERSION &&
    pip-compile --upgrade \
        dev/hierarchy/requirements-base.in \
        -o dev/$PYTHON_VERSION/requirements.txt &&
    pip-compile --upgrade \
        dev/$PYTHON_VERSION/requirements.txt \
        dev/hierarchy/requirements-doc.in \
        -o dev/$PYTHON_VERSION/requirements-doc.txt &&
    pip-compile --upgrade \
        dev/$PYTHON_VERSION/requirements.txt \
        dev/hierarchy/requirements-test.in \
        -o dev/$PYTHON_VERSION/requirements-test.txt &&
    pip-compile --upgrade \
        dev/$PYTHON_VERSION/requirements.txt \
        dev/$PYTHON_VERSION/requirements-test.txt \
        dev/hierarchy/requirements-sty.in \
        -o dev/$PYTHON_VERSION/requirements-sty.txt &&
    pip-compile --upgrade \
        dev/$PYTHON_VERSION/requirements.txt \
        dev/hierarchy/requirements-doc.in \
        dev/$PYTHON_VERSION/requirements-test.txt \
        dev/$PYTHON_VERSION/requirements-sty.txt \
        dev/hierarchy/requirements-dev.in \
        -o dev/$PYTHON_VERSION/requirements-dev.txt &&
    pip install \
        -r dev/$PYTHON_VERSION/requirements.txt \
        -r dev/$PYTHON_VERSION/requirements-doc.txt \
        -r dev/$PYTHON_VERSION/requirements-test.txt \
        -r dev/$PYTHON_VERSION/requirements-sty.txt \
        -r dev/$PYTHON_VERSION/requirements-dev.txt &&
    exit 0

exit 1 # if failure
