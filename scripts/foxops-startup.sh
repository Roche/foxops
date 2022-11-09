#!/bin/bash

# patch doorkeeper oidc config to use http protocols for uri's
OIDC_CONF=/opt/gitlab/embedded/service/gitlab-rails/config/initializers/doorkeeper_openid_connect.rb
TMPFILE=$(/bin/tempfile)
cat ${OIDC_CONF} | sed -e 's/issuer\(.*\)/issuer\1\n\n  protocol do\n    :http\n  end\n/' > ${TMPFILE}
chown --reference=${OIDC_CONF} ${TMPFILE}
chmod --reference=${OIDC_CONF} ${TMPFILE}
mv -f ${TMPFILE} ${OIDC_CONF}

# real gitlab startup command
exec /assets/wrapper "$@"

