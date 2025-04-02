export interface AuthorizationToken {
    token: string,
    user: string,
    groups: string[] | null | undefined | string,
}
