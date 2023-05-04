import { IncarnationBaseApiView } from 'interfaces/incarnations.types'
import { convertToUiBaseIncarnation } from '../services/incarnations'
import { searchIncarnations } from './search-incarnations'

const data: IncarnationBaseApiView[] = [
  {
    id: 910,
    incarnation_repository: 'repo1',
    target_directory: 'dir/1',
    commit_sha: 'a',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/a',
    merge_request_id: null,
    merge_request_url: null,
    template_repository: 'repo1',
    created_at: '2021-01-01T00:00:00.000Z',
    requested_version: 'test-version',
    revision: 1,
    type: 'direct'
  },
  {
    id: 1632,
    incarnation_repository: 'repo2',
    target_directory: 'dir/3',
    commit_sha: 'b',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/b',
    merge_request_id: null,
    merge_request_url: null,
    template_repository: 'repo2',
    created_at: '2021-01-01T00:00:00.000Z',
    requested_version: 'test-version',
    revision: 1,
    type: 'merge_request'
  },
  {
    id: 659,
    incarnation_repository: 'repo5',
    target_directory: 'dir/5',
    commit_sha: 'e',
    commit_url: 'https://some-gitlab-registry.com/some-repo/-/commit/e',
    merge_request_id: '1',
    merge_request_url: 'https://some-gitlab-registry.com/some-repo/-/merge_requests/1',
    template_repository: 'repo2',
    created_at: '2021-02-01T00:00:00.000Z',
    requested_version: 'test-version',
    revision: 2,
    type: 'direct'
  },
  {
    id: 1636,
    incarnation_repository: 'repo3',
    target_directory: 'dir/2',
    commit_sha: 'c',
    commit_url: 'https://some-gitlab-registry.com/commit/-/commit/c',
    merge_request_id: '1',
    merge_request_url: 'https://some-gitlab-registry.com/commit/-/merge_requests/1',
    template_repository: 'repo3',
    created_at: '2021-01-01T00:00:00.000Z',
    requested_version: 'test-version',
    revision: 1,
    type: 'merge_request'
  },
  {
    id: 1337,
    incarnation_repository: 'repo4',
    target_directory: 'dir/4',
    commit_sha: 'd',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/d',
    merge_request_id: '2373',
    merge_request_url: 'https://some-gitlab-registry.com/repo/-/merge_requests/2373',
    template_repository: 'repo2',
    created_at: '2021-01-01T00:00:00.000Z',
    requested_version: 'test-version',
    revision: 1,
    type: 'merge_request'
  }
]

const _data = data.map(convertToUiBaseIncarnation).map((x, i) => ({
  ...x,
  templateVersion: i === 0 ? '' : i > 2 ? `non-semantic-version-${i}` : `${i}.0.0`
}))

describe('searchSortIncarnations', () => {
  it('shouldn\'t filter when search is an empty string', () => {
    const result = searchIncarnations(_data, { search: '' })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1',
      'repo2',
      'repo5',
      'repo3',
      'repo4'
    ])
  })
  it('should search by incarnation repository', () => {
    const result = searchIncarnations(_data, { search: 'repo1' })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1'
    ])
  })
  it('should search by target directory', () => {
    const result = searchIncarnations(_data, { search: 'dir/1' })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1'
    ])
  })
  it('should search by merge request url', () => {
    const result = searchIncarnations(_data, { search: '2373' })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo4'
    ])
  })
})
