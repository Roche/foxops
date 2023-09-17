#!/usr/bin/env sh

printf 'Waiting for GitLab container to become healthy'

until test -n "$(docker ps --quiet --filter label=foxops-gitlab/owned --filter health=healthy)"; do
  printf '.'
  sleep 5
done

echo
echo 'GitLab is healthy'
