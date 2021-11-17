#!/usr/bin/env bash
sessionfile=/bot/data/*.session
if [[ ! -e sessionfile ]]
then
    echo " Telegram: You are not authorized. Your code:"
    curl http://127.0.0.1:5000/api/bot/getcode
    read -r code
    data="{\"code\":$code}"
else
    data="{}"
fi
curl -H "Content-Type: application/json" --data $data http://127.0.0.1:5000/api/bot/initialize
