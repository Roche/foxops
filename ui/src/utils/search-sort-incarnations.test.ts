import { convertToUiBaseIncarnation, IncarnationBaseApiView } from '../services/incarnations'
import { searchSortIncarnations } from './search-incarnations'

const data: IncarnationBaseApiView[] = [
  {
    id: 910,
    incarnation_repository: 'repo1',
    target_directory: 'dir/1',
    commit_sha: 'a',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/a',
    merge_request_id: null,
    merge_request_url: null
  },
  {
    id: 1632,
    incarnation_repository: 'repo2',
    target_directory: 'dir/3',
    commit_sha: 'b',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/b',
    merge_request_id: null,
    merge_request_url: null
  },
  {
    id: 659,
    incarnation_repository: 'repo5',
    target_directory: 'dir/5',
    commit_sha: 'e',
    commit_url: 'https://some-gitlab-registry.com/some-repo/-/commit/e',
    merge_request_id: '1',
    merge_request_url: 'https://some-gitlab-registry.com/some-repo/-/merge_requests/1'
  },
  {
    id: 1636,
    incarnation_repository: 'repo3',
    target_directory: 'dir/2',
    commit_sha: 'c',
    commit_url: 'https://some-gitlab-registry.com/commit/-/commit/c',
    merge_request_id: '1',
    merge_request_url: 'https://some-gitlab-registry.com/commit/-/merge_requests/1'
  },
  {
    id: 1337,
    incarnation_repository: 'repo4',
    target_directory: 'dir/4',
    commit_sha: 'd',
    commit_url: 'https://some-gitlab-registry.com/repo/-/commit/d',
    merge_request_id: '2373',
    merge_request_url: 'https://some-gitlab-registry.com/repo/-/merge_requests/2373'
  }
]

const _data = data.map(convertToUiBaseIncarnation).map((x, i) => ({
  ...x,
  templateVersion: i === 0 ? '' : i > 2 ? `non-semantic-version-${i}` : `${i}.0.0`
}))

describe('searchSortIncarnations', () => {
  it('should sort by incarnation repository', () => {
    let result = searchSortIncarnations(_data, { search: '', sort: 'incarnationRepository', asc: true })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1',
      'repo2',
      'repo3',
      'repo4',
      'repo5'
    ])
    result = searchSortIncarnations(_data, { search: '', sort: 'incarnationRepository', asc: false })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1',
      'repo2',
      'repo3',
      'repo4',
      'repo5'
    ].reverse())
  })
  it('should sort by target directory', () => {
    let result = searchSortIncarnations(_data, { search: '', sort: 'targetDirectory', asc: true })
    expect(result.map(x => x.targetDirectory)).toEqual([
      'dir/1',
      'dir/2',
      'dir/3',
      'dir/4',
      'dir/5'
    ])
    result = searchSortIncarnations(_data, { search: '', sort: 'targetDirectory', asc: false })
    expect(result.map(x => x.targetDirectory)).toEqual([
      'dir/1',
      'dir/2',
      'dir/3',
      'dir/4',
      'dir/5'
    ].reverse())
  })
  it('should sort by template version', () => {
    let result = searchSortIncarnations(_data, { search: '', sort: 'templateVersion', asc: true })
    expect(result.map(x => x.templateVersion)).toEqual([
      '1.0.0',
      '2.0.0',
      'non-semantic-version-3',
      'non-semantic-version-4',
      ''
    ])
    result = searchSortIncarnations(_data, { search: '', sort: 'templateVersion', asc: false })
    expect(result.map(x => x.templateVersion)).toEqual([
      'non-semantic-version-4',
      'non-semantic-version-3',
      '2.0.0',
      '1.0.0',
      ''
    ])
  })
  it('should search by incarnation repository, search is a string', () => {
    const result = searchSortIncarnations(_data, { search: 'repo1', sort: 'targetDirectory', asc: true })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1'
    ])
    expect(result.length).toEqual(1)
  })
  it('should search by incarnation repository, search is a regex', () => {
    const result = searchSortIncarnations(_data, { search: '^r.*o[1-2]$', sort: 'incarnationRepository', asc: true })
    expect(result.map(x => x.incarnationRepository)).toEqual([
      'repo1',
      'repo2'
    ])
    expect(result.length).toEqual(2)
  })
})
