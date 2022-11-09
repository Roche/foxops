#!/usr/bin/env sh

printf 'Waiting for GitLab container to become healthy'

gitlab_container=$(docker ps --quiet --filter label=foxops-gitlab/owned)

# wait until log is available in container
echo
docker exec $gitlab_container sh -c 'while [ ! -f  /tmp/gitlab-acctest.log ]; do printf "."; sleep 5; done'

# log message from setup script
echo
docker exec $gitlab_container tail --follow=name --quiet /tmp/gitlab-acctest.log 2>/dev/null

# wait until really healthy
until test -n "$(docker ps --quiet --filter label=foxops-gitlab/owned --filter health=healthy)"; do
  printf '.'
  sleep 5
done

echo
echo 'GitLab is healthy'

# Print the version, since it is useful debugging information.
curl --silent --show-error --header 'Authorization: Bearer ACCTEST1234567890123' http://${GITLAB_HOST:-127.0.0.1}:${GITLAB_PORT:-5002}/api/v4/version
echo
