#!/usr/bin/env sh

# This script is intended to be used as a Docker HEALTHCHECK for the GitLab container.
# It prepares GitLab prior to running acceptance tests.
#
# This is a known workaround for docker-compose lacking lifecycle hooks.
# See: https://github.com/docker/compose/issues/1809#issuecomment-657815188

set -e

# if already running just exit - avoid conflict if two instances are running in parallel
# in case of error with rails happening just once and because of set -e the running file
# will not be cleaned up and this script will always exit 1 - the container will never
# become healthy => timeout after 30min in github workflow
running=/var/gitlab-acctest-running
test -f $running && exit 1

# Check for a successful HTTP status code from GitLab.
curl --silent --show-error --fail --output /dev/null 127.0.0.1:80

# Because this script runs on a regular health check interval,
# this file functions as a marker that tells us if initialization already finished.
done=/var/gitlab-acctest-initialized

test -f $done || {
  echo 'Initializing GitLab for acceptance tests'

  # running
  touch $running

  echo 'Creating access token'
  (
    printf 'terraform_token = PersonalAccessToken.create('
    printf 'user_id: 1, '
    printf 'scopes: [:api, :read_user], '
    printf 'name: :terraform);'
    printf "terraform_token.set_token('ACCTEST1234567890123');"
    printf 'terraform_token.save!;'
  ) | gitlab-rails runner -

  echo 'Creating oauth application'
  (
    printf 'foxops_app = Doorkeeper::Application.create('
    printf 'id: 1, '
    printf 'name: "foxops", '
    printf 'uid: "1234567890abcdeffedcba0987654321", '
    printf 'secret: "FOXOPS1234567890", '
    printf 'redirect_uri: "http://127.0.0.1:5001/login\r\nhttp://127.0.0.1:5001/auth/token", '
    printf 'scopes: "api openid profile email", '
    printf 'owner_id: 1, '
    printf 'owner_type: "User", '
    printf 'trusted: true, '
    printf 'confidential: true);'
    printf 'foxops_app.save!;'
  ) | gitlab-rails runner -

  echo 'Creating test user'
  (
    printf 'foxy = User.create('
    printf 'name: "Foxops Test user", '
    printf 'username: "foxy", '
    printf 'password: "xxx123yyy", '
    printf 'email: "foxy@foxops.io", '
    printf 'skip_confirmation: true);'
    printf 'foxy.save!;'
  ) | gitlab-rails runner -
  
  # 2020-09-07: Currently Gitlab (version 13.3.6 ) doesn't allow in admin API
  # ability to set a group as instance level templates.
  # To test resource_gitlab_project_test template features we add
  # group, project myrails and admin settings directly in scripts/start-gitlab.sh
  # Once Gitlab add admin template in API we could manage group/project/settings
  # directly in tests like TestAccGitlabProject_basic.
  # Works on CE too

  echo 'Creating an instance level template group with a simple template based on rails'
  (
    printf 'group_template = Group.new('
    printf 'name: :terraform, '
    printf 'path: :terraform);'
    printf 'group_template.save!;'
    printf 'application_settings = ApplicationSetting.find_by "";'
    printf 'application_settings.custom_project_templates_group_id = group_template.id;'
    printf 'application_settings.save!;'
    printf 'attrs = {'
    printf 'name: :myrails, '
    printf 'path: :myrails, '
    printf 'namespace_id: group_template.id, '
    printf 'template_name: :rails, '
    printf 'id: 999};'
    printf 'project = ::Projects::CreateService.new(User.find_by_username("root"), attrs).execute;'
    printf 'project.saved?;'
  ) | gitlab-rails runner -

  rm -f $running
  touch $done
}

echo 'GitLab is ready for acceptance tests'
