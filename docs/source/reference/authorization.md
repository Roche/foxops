# Authorization
FoxOps  supports an authorization system that introduces the concept of users and groups. This allows for limiting access to certain incarnations based on the user or group.

```{admonition} Missing Authentification
:class: caution
The current authorization system doesn't yet check if the provided users or groups are valid. Additionally, the current static API token is shared between all users, making it technically possible to access all incarnations with the API token.

This can currently be fixed by using an external component to authenticate a request. While this is a limitation, it is planned to integrate FoxOps with an external SSO service, which would remove this limitation.
```

Currently, each incoming request expects three different headers

| Header | Description | Required |
| ----- | ----------- | -------- |
| `Authorization` | The static API token which is used to authenticate the request. This token can be set with the `FOXOPS_STATIC_TOKEN` environment variable. | ✓ |
| `User` | The user which is used to authenticate the request. This user is checked to see if they have access to the requested incarnation. | ✓ |
| `Groups` | The groups which are used to authenticate the request. These groups are checked to see if the user has access to the requested incarnation. This header can also be provided empty or omitted. | X |

## User/Group Creation
User and groups get automatically created when a request is made to the API. This means that if a user or group doesn't exist, it will be created automatically. The newly create users don't have admin rights by default.

However there exists a default user in the database (`root`), which has admin rights. This user is created automatically when the database is initialized. 


## Basic Authorization Concepts
As previously mentioned, FoxOps uses the provided HTTP headers (`User` and `Groups`) to authorize incoming requests.

### User
A FoxOps user is uniquely identified by its username. It is also the username that can be used to authorize an incoming request. 

### Groups
Groups in FoxOps are uniquely identified by their system name. This system name can differ from the display name. A group can have zero or more users.


### Incarnation
An Incarnation always has a User as an owner. This user is permitted to perform all actions on the Incarnation. It is also possible to assign different users or groups privileges on the Incarnation. These privileges can either be read or write (which also includes read) permissions.


### Change
The change model now also stores which user initialized said change. However, it is not possible to give certain groups or users permissions on a change. The change permission is managed by the Incarnation to which the change belongs.


### Access Control
The following endpoints are protected with an authorization layer, which requires certain rights.

```{admonition} Access Control
Users which have admin rights are allowed to perform any actions on any endpoints.
```

| Endpoint | Method | Required Permission |
| -------- | ------ | ------------------- |
| `/incarnations` | GET | only returns the Incarnations, to which the User has either read permission or is the owner |
| `/incarnations/{id}` | GET | read or is the owner |
| `/incarnations` | POST | No permissions required. However the current user automatically becomes the owner of the newly created Incarnation. |
| `/incarnations/{id}` | PUT | write or is the owner |
| `/incarnations/{id}` | DELETE | write or is the owner |
| `/incarnations/{id}` | PATCH | write or is the owner |
| `/incarnations/{id}/reset` | POST | write or is the owner |
| `/incarnations/{id}/diff` | GET | read or is the owner |
| `/incarnations/{id}/changes` | GET | read or is the owner |
| `/incarnations/{id}/changes` | POST | write or is the owner |
| `/incarnations/{id}/changes/{revision}` | GET | read or is the owner |
| `/incarnations/{id}/changes/{revision}/fix` | POST | write or is the owner |
| `/user` | GET | Admin only |
| `/user/{id}` | GET | Admin only |
| `/user/{id}` | PATCH | Admin only |
| `/user/{id}` | DELETE | Admin only |
| `/group` | GET | Admin only |
| `/group/{id}` | GET | Admin only |
| `/group/{id}` | PATCH | Admin only |
| `/group/{id}` | DELETE | Admin only |

## Productive Setup
While the FoxOps API currently doesn't authenticate the User and Groups headers, it is still possible to use this setup in a productive environment. An example of such a setup is described below.

The following mermaid diagram describes the setup of FoxOps with an external SSO service and a reverse proxy. The reverse proxy is used to authenticate the user and add the User and Groups headers to the request. This ensures that the provided user and groups are valid.

```{mermaid}
graph TD
    A[Client/User]
    B[SSO Service]
    C[Reverse Proxy]
    D[FoxOps API]

    A --> |1. Login and request JWT| B
    B --> |2. JWT| A
    A --> |3. Request FoxOps API with JWT| C
    C --> |4. Validates JWT| C 
    C --> |5. Request FoxOps API with Headers| D
    D --> |6. Response| C
    C --> |6. Response| A
```

### 1. Login and request JWT
The first step in this setup is to request a new JWT token from the SSO service. An example of such a service would be [Keycloak](https://www.keycloak.org/).

### 2. JWT
The SSO service then responds with a signed JWT token. This token contains the user and group information.

### 3. Request FoxOps API with JWT
The client then requests the FoxOps API with the JWT token. This token is used to authenticate the user and groups. The client does **not** provide any of the required headers for the FoxOps API.

### 4. Validates JWT
The reverse proxy then validates the JWT signature. It parses the user and group information from the JWT token.

### 5. Request FoxOps API with Headers
The reverse proxy then requests the FoxOps API. It provides the three required headers:
* Authorization: _Static API Token configured in the Reverse Proxy_
* User: _User from the JWT token_
* Groups: _Groups from the JWT token_

### 6. Response
The API uses the provided user and groups to check if the user has access to the requested incarnation. If the user has access, the API returns the response to the reverse proxy. The reverse proxy then returns the response to the client.
