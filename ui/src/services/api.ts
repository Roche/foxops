interface MakeRequestOptions<Req, Res> {
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  body?: Req,
  authorized?: boolean,
  mockedData?: Res
}

type MakeRequestFunc = <Req, Res>(options: MakeRequestOptions<Req, Res>) => Promise<Res>
type RequestFunc = <Req, Res>(options: Omit<MakeRequestOptions<Req, Res>, 'method'>) => Promise<Res>

interface API {
  token: string | null,
  setToken: (token: string | null) => void,
  makeRequest: MakeRequestFunc
  get: RequestFunc,
  post: RequestFunc,
  makeUrl: (path: string) => string,
}

const API_PREFIX = '/api'
export const api: API = {
  token: null,
  setToken: (token: string | null) => {
    api.token = token
  },
  makeUrl: (path: string) => `${process.env.FOXOPS_API_URL ?? ''}${API_PREFIX}${path}`,
  makeRequest: async <Req, Res>({
    url,
    method,
    body,
    authorized = true,
    mockedData
  }: MakeRequestOptions<Req, Res>): Promise<Res> => {
    // handle headers stuff
    const headers = new Headers()
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
    const response = await fetch(api.makeUrl(url), {
      method,
      body: requestBody,
      headers
    })

    // handle response
    const result = await response.json()
    return result as Res
  },
  get: <Req, Res>(options: Omit<MakeRequestOptions<Req, Res>, 'method'>): Promise<Res> => api.makeRequest({
    ...options,
    method: 'GET'
  }),
  post: <Req, Res>(options: Omit<MakeRequestOptions<Req, Res>, 'method'>): Promise<Res> => api.makeRequest({
    ...options,
    method: 'POST'
  })
}
