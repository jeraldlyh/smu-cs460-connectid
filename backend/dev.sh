#!/bin/sh

export FLASK_APP=main
export ENV=development

flask run --debugger
