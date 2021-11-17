#!/bin/sh

pipenv run hypercorn src.app:app --bind 0.0.0.0:5000 --reload

