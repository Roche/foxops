type Formats = 'json' | 'text';

interface MakeRequestOptions<Req, Res> {
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  body?: Req,
  authorized?: boolean,
  mockedData?: Res,
  isApi?: boolean,
  format?: Formats,
}

type MakeRequestFunc = <Req, Res>(options: MakeRequestOptions<Req, Res>) => Promise<Res>
type RequestFunc = <Req, Res>(url: string, options?: Omit<MakeRequestOptions<Req, Res>, 'method' | 'url'>) => Promise<Res>

interface API {
  token: string | null,
  setToken: (token: string | null) => void,
  makeRequest: MakeRequestFunc
  get: RequestFunc,
  post: RequestFunc,
  makeUrl: (path: string, isApi: boolean) => string,
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
  setToken: (token: string | null) => {
    api.token = token
  },
  makeUrl: (path: string, isApi: boolean) => `${process.env.FOXOPS_API_URL ?? ''}${isApi ? API_PREFIX : ''}${path}`,
  makeRequest: async <Req, Res>({
    url,
    method,
    body,
    authorized = true,
    isApi = true,
    mockedData,
    format = 'json'
  }: MakeRequestOptions<Req, Res>): Promise<Res> => {
    // handle headers stuff
    const headers = new Headers([
      ['Content-Type', 'application/json']
    ])
    if (authorized) {
      if (!api.token) throw new Error('No token provided for authorized request')
      headers.append('Authorization', `Bearer ${api.token}`)
    }

    // handle request body stuff
    const requestBody = body ? JSON.stringify(body) : undefined

    // mock stuff for not ready API
    if (mockedData) {
      return Promise.resolve(mockedData)
    }
    // make request
    const response = await fetch(api.makeUrl(url, isApi), {
      method,
      body: requestBody,
      headers
    })

    // handle response
    const result = await (format === 'json' ? response.json() : response.text())
    if (!response.ok) {
      throw {
        status: response.status,
        ...result as ApiErrorResponse
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
  })
}
