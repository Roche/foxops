#!/usr/bin/env sh

printf 'Waiting for GitLab container to become healthy'

until test -n "$(docker ps --quiet --filter label=foxops-gitlab/owned --filter health=healthy)"; do
  printf '.'
  sleep 5
done

echo
echo 'GitLab is healthy'

# Print the version, since it is useful debugging information.
curl --silent --show-error --header 'Authorization: Bearer ACCTEST1234567890123' http://${GITLAB_HOST:-127.0.0.1}:${GITLAB_PORT:-5002}/api/v4/version
echo
