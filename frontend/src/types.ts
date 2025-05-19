import type { ViteSSGContext } from 'vite-ssg'

export type UserModule = (ctx: ViteSSGContext) => void

export interface IResult {
  id: string
  creator: string[]
  dateCreated: string
  datePublished: string
  lastModified: string
  description: string
  highlights: {
    path: string
    score: number
    texts: {
      type: string
      value: string
    }[]
  }[]
  license: string
  keywords: string[]
  name: string
  score: number // unused for now...
  url: string
  funding: string[]
  spatialCoverage: any
  _showMore?: boolean // Used to toggle 'show more...' button
}

export interface ISearchApiResponse {
  docs: any[]
  meta?: { count?: { total: number } }
}

export interface ISearchResultsMetadata {
  count?: { total: number }
}

export interface IHint {
  type: 'db' | 'local'
  key: string
}

export interface ISearchFilter {
  publicationYear: {
    min: number
    max: number
    isActive: boolean
  }
  creationDate: {
    min: number
    max: number
    isActive: boolean
  }
  dataCoverage: {
    min: number
    max: number
    isActive: boolean
  }
  contentType: {
    options: string[]
    value: string[] | null
    isActive: boolean
  }
  availability: {
    options: string[]
    value: string[] | null
    isActive: boolean
  }
  authorName: string
  contributorName: string
  ownerName: string
  subject: string
  funder: string
}

export interface ISearchParams {
  term: string
  pageSize: number
  pageNumber: number
  publishedStart?: number
  publishedEnd?: number
  creationDateStart?: number
  creationDateEnd?: number
  dataCoverageStart?: number
  dataCoverageEnd?: number
  authorName?: string
  contributorName?: string
  ownerName?: string
  funder?: string
  subject?: string
  availability?: string[]
  contentType?: string[]
  sortBy?: 'name' | 'dateCreated' | 'relevance'
}

export interface ITypeaheadParams {
  term: string
}

export enum EnumShortParams {
  QUERY = 'q',
  AUTHOR_NAME = 'an',
  CONTENT_TYPE = 'ct',
  CONTRIBUTOR_NAME = 'cn',
  OWNER_NAME = 'on',
  FUNDER = 'f',
  SUBJECT = 'sj',
  AVAILABILITY = 'a',
  CREATION_DATE = 'cd',
  PUBLICATION_YEAR = 'py',
  DATA_COVERAGE = 'dc',
  SORT = 's',
}

export type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
}
