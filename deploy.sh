#!/bin/bash
echo Enter Username:
read username
echo Enter Password:
read password
export username
export password
docker compose up -d