import { AuthorizationToken } from 'interfaces/authz.types'

type Formats = 'json' | 'text';

interface MakeRequestOptions<Req, Res> {
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  body?: Req,
  authorized?: boolean,
  mockedData?: Res,
  apiPrefix?: string,
  format?: Formats,
}

type MakeRequestFunc = <Req, Res>(options: MakeRequestOptions<Req, Res>) => Promise<Res>
type RequestFunc = <Req, Res>(url: string, options?: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'>) => Promise<Res>

interface API {
  token: AuthorizationToken | null,
  setToken: (token: AuthorizationToken | null) => void,
  makeRequest: MakeRequestFunc
  get: RequestFunc,
  post: RequestFunc,
  put: RequestFunc,
  delete: RequestFunc,
  patch: RequestFunc,
  makeUrl: (path: string, apiPrefix: string) => string,
}

const API_PREFIX = '/api'

interface ApiError {
  status: number,
  message: string
}

export interface ApiErrorResponse {
  documentation: null | string,
  message: string,
}
export const api: API = {
  token: null,
  setToken: (token: AuthorizationToken | null) => {
    api.token = token
  },
  makeUrl: (path, apiPrefix) => `${process.env.FOXOPS_API_URL ?? ''}${apiPrefix}${path}`,
  makeRequest: async <Req, Res>({
    url,
    method,
    body,
    authorized = true,
    apiPrefix = API_PREFIX,
    mockedData,
    format = 'json'
  }: MakeRequestOptions<Req, Res>): Promise<Res> => {
    // handle headers stuff
    const headers = new Headers([
      ['Content-Type', 'application/json']
    ])
    if (authorized) {
      if (!api.token) throw new Error('No token provided for authorized request')
      headers.append('Authorization', `Bearer ${api.token.token}`)
      headers.append('User', api.token.user)
      const groups = api.token.groups
      if (groups) {
        if (typeof groups === 'string') {
          headers.append('Groups', groups)
        } else {
          headers.append('Groups', groups.join(','))
        }
      }
    }

    // handle request body stuff
    const requestBody = body ? JSON.stringify(body) : undefined

    // mock stuff for not ready API
    if (mockedData) {
      return Promise.resolve(mockedData)
    }
    // make request
    const response = await fetch(api.makeUrl(url, apiPrefix), {
      method,
      body: requestBody,
      headers
    })

    // handle response
    const result = await (format === 'json' ? response.json() : response.text())
    if (!response.ok) {
      // FIXME: this is mess, should be removed as soon as auth/test will start to respond with JSON
      let errorResult = result
      try {
        errorResult = typeof errorResult === 'string' ? JSON.parse(errorResult) : errorResult
      } catch (error) {
        errorResult = {
          message: errorResult
        }
      }
      throw {
        status: response.status,
        ...errorResult as ApiErrorResponse
      } as ApiError
    }
    return result as Res
  },
  get: <Req, Res>(url: string, options: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'> = {}): Promise<Res> => api.makeRequest({
    url,
    ...options,
    method: 'GET'
  }),
  post: <Req, Res>(url: string, options: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'> = {}): Promise<Res> => api.makeRequest({
    url,
    ...options,
    method: 'POST'
  }),
  put: <Req, Res>(url: string, options: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'> = {}): Promise<Res> => api.makeRequest({
    url,
    ...options,
    method: 'PUT'
  }),
  delete: <Req, Res>(url: string, options: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'> = {}): Promise<Res> => api.makeRequest({
    url,
    ...options,
    method: 'DELETE'
  }),
  patch: <Req, Res>(url: string, options: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'> = {}): Promise<Res> => api.makeRequest({
    url,
    ...options,
    method: 'PATCH'
  })
}
