#!/bin/bash
echo Enter Username:
read username
echo Enter Password:
read password
export username=username
export password=username
docker compose up -d