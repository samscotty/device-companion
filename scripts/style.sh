#!/bin/sh
set -eux
targets="src tests"

black --check --diff ${targets} || exit
isort --check --diff ${targets} || exit
flake8 ${targets} || exit
mypy --no-error-summary ${targets} || exit
