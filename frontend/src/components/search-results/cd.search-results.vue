<script lang="ts">
import type {
  EnumDictionary,
  IResult,
  ISearchFilter,
  ISearchParams,
  ISearchResultsMetadata,
} from '@/types'
import type { LoaderOptions } from 'google-maps'
import CdSpatialCoverageMap from '@/components/search-results/cd.spatial-coverage-map.vue'
import CdSearch from '@/components/search/cd.search.vue'
import { MAX_YEAR, MIN_YEAR, sameRouteNavigationErrorHandler } from '@/constants'
import SearchHistory from '@/models/search-history.model'
import SearchResults from '@/models/search-results.model'
import Search from '@/models/search.model'
import {
  EnumShortParams,
} from '@/types'
import { formatDate } from '@/util'
import { Notifications } from '@cznethub/cznet-vue-core'
import { Loader } from 'google-maps'
import { Component, toNative, Vue } from 'vue-facing-decorator'
import { useRoute, useRouter } from 'vue-router'
import CdRangeInput from './cd.range-input.vue'

const options: LoaderOptions = { libraries: ['drawing'] }
const loader: Loader = new Loader(
  import.meta.env.VITE_APP_GOOGLE_MAPS_API_KEY,
  options,
)

const sortOptions: { label: string, value: string }[] = [
  { label: 'Relevance', value: 'relevance' },
  { label: 'Date Created', value: 'dateCreated' },
  { label: 'Title', value: 'name' },
]

@Component({
  name: 'cd-search-results',
  components: { CdSearch, CdSpatialCoverageMap, CdRangeInput },
})
class CdSearchResults extends Vue {
  loader = loader
  options = options
  isIntersecting = false
  searchQuery = ''
  pageNumber = 1
  pageSize = 15
  hasMore = true
  isSearching = false
  isFetchingMore = false
  sort: 'name' | 'dateCreated' | 'relevance' = 'relevance'
  sortEmpty = 'dateCreated'
  // public view: 'list' | 'map' = 'list'
  filter: ISearchFilter = {
    publicationYear: {
      min: MIN_YEAR,
      max: MAX_YEAR,
      isActive: false,
    },
    creationDate: {
      min: MIN_YEAR,
      max: MAX_YEAR,
      isActive: false,
    },
    dataCoverage: {
      min: MIN_YEAR,
      max: MAX_YEAR,
      isActive: false,
    },
    contentType: {
      options: [
        'Collection',
        'CSV Data',
        'Document',
        'File Set',
        'Generic Data',
        'Geographic Feature (ESRI Shapefiles)',
        'Geographic Raster',
        'Image',
      ],
      value: null,
      isActive: false,
    },

    availability: {
      options: ['Discoverable', 'Public', 'Published'],
      value: null,
      isActive: false,
    },
    authorName: '',
    contributorName: '',
    ownerName: '',
    subject: '',
    funder: '',
  }

  availabilityIcons = [
    { icon: 'mdi-lock-open', size: 'small', color: 'orange-darken-2' }, // Discoverable
    { icon: 'mdi-lock', size: 'small', color: 'green-darken-2' }, // Public
    { icon: 'mdi-feather', class: 'pl-1', color: 'green-darken-2' }, // Published
  ]

  // items = [
  //   {
  //     icons: "",
  //     title: "Logan GAMUT field operations database",
  //     firstAuthor: "GeoTrust CDM",
  //     dateCreated: new Date(),
  //     lastModified: new Date(),
  //   },
  // ];

  headers = reactive([
    { title: '', key: 'icons', visible: true },
    { title: 'Title', key: 'title', visible: true, minWidth: 200 },
    {
      title: 'First Author',
      key: 'firstAuthor',
      visible: true,
      minWidth: 200,
    },
    {
      title: 'Date Created',
      key: 'dateCreated',
      visible: true,
      minWidth: 200,
    },
    {
      title: 'Last Modified',
      key: 'lastModified',
      visible: true,
      minWidth: 200,
    },
  ])

  formatDate = formatDate
  route = useRoute()
  router = useRouter()

  get sortOptions(): { label: string, value: string }[] {
    return this.searchQuery
      ? sortOptions
      : sortOptions.slice(1, sortOptions.length)
  }

  get searchResultsMetadata(): ISearchResultsMetadata | undefined {
    return Search.$state.results.metadata
  }

  public get creationDate() {
    return SearchResults.$state.creationDate
  }

  public set creationDate(range: [number, number]) {
    // TODO: validate input
    SearchResults.commit((state) => {
      state.creationDate = range
    })
  }

  public get publicationYear() {
    return SearchResults.$state.publicationYear
  }

  public set publicationYear(range: [number, number]) {
    // TODO: validate input
    SearchResults.commit((state) => {
      state.publicationYear = range
    })
  }

  public get dataCoverage() {
    return SearchResults.$state.dataCoverage
  }

  public set dataCoverage(range: [number, number]) {
    // TODO: validate input
    SearchResults.commit((state) => {
      state.dataCoverage = range
    })
  }

  public get panels() {
    return SearchResults.$state.panels
  }

  public set panels(range: number[]) {
    // TODO: validate input
    SearchResults.commit((state) => {
      state.panels = range
    })
  }

  public get results(): IResult[] {
    return Search.$state.results.docs
  }

  // public get clusters() {
  //   return Search.$state.clusters;
  // }

  public get isSomeFilterActive() {
    return (
      this.filter.creationDate.isActive
      || this.filter.publicationYear.isActive
      || this.filter.dataCoverage.isActive
      || (this.filter.availability.isActive
        && this.filter.availability.value?.length)
      || (this.filter.contentType.isActive
        && this.filter.contentType.value?.length)
      || this.filter.authorName
      || this.filter.contributorName
      || this.filter.ownerName
      || this.filter.subject
      || this.filter.funder
    )
  }

  /** Search query parameters */
  get queryParams(): ISearchParams {
    const queryParams: ISearchParams = {
      term: this.searchQuery,
      pageSize: this.pageSize,
      pageNumber: this.pageNumber,
    }

    // CREATION DATE
    if (this.filter.creationDate.isActive) {
      queryParams.creationDateStart = this.creationDate[0]
      queryParams.creationDateEnd = this.creationDate[1]
    }

    // PUBLICATION YEAR
    if (this.filter.publicationYear.isActive) {
      queryParams.publishedStart = this.publicationYear[0]
      queryParams.publishedEnd = this.publicationYear[1]
    }

    // DATA COVERAGE
    if (this.filter.dataCoverage.isActive) {
      queryParams.dataCoverageStart = this.dataCoverage[0]
      queryParams.dataCoverageEnd = this.dataCoverage[1]
    }

    // CREATOR NAME
    if (this.filter.authorName) {
      queryParams.authorName = this.filter.authorName
    }

    if (this.filter.contributorName) {
      queryParams.authorName = this.filter.contributorName
    }

    if (this.filter.ownerName) {
      queryParams.authorName = this.filter.ownerName
    }

    if (this.filter.funder) {
      queryParams.authorName = this.filter.funder
    }

    if (this.filter.subject) {
      queryParams.subject = this.filter.subject
    }

    // AVAILABILITY
    if (this.filter.availability.isActive && this.filter.availability.value) {
      queryParams.availability = this.filter.availability.value
    }

    // CONTENT TYPE
    if (
      this.filter.contentType.isActive
      && this.filter.contentType.value?.length
    ) {
      queryParams.contentType = this.filter.contentType.value
    }

    // SORT BY
    if (this.searchQuery && this.sort) {
      queryParams.sortBy = this.sort
    }
    else if (this.sortEmpty) {
      // @ts-ignore
      queryParams.sortBy = this.sortEmpty
    }

    return queryParams
  }

  /** Route query parameters with short keys. These are parameters needed to replicate a search. */
  public get routeParams(): EnumDictionary<EnumShortParams, any> {
    return {
      [EnumShortParams.QUERY]: this.searchQuery,
      [EnumShortParams.AUTHOR_NAME]: this.filter.authorName || undefined,
      [EnumShortParams.CONTRIBUTOR_NAME]:
        this.filter.contributorName || undefined,
      [EnumShortParams.OWNER_NAME]: this.filter.ownerName || undefined,
      [EnumShortParams.FUNDER]: this.filter.funder || undefined,
      [EnumShortParams.SUBJECT]: this.filter.subject || undefined,
      [EnumShortParams.AVAILABILITY]: this.filter.availability.isActive
        ? this.filter.availability.value || undefined
        : undefined,
      [EnumShortParams.CONTENT_TYPE]: this.filter.contentType.isActive
        ? this.filter.contentType.value || undefined
        : undefined,
      [EnumShortParams.CREATION_DATE]: this.filter.creationDate.isActive
        ? this.creationDate.map(n => n.toString()) || undefined
        : undefined,
      [EnumShortParams.PUBLICATION_YEAR]: this.filter.publicationYear.isActive
        ? this.publicationYear.map(n => n.toString()) || undefined
        : undefined,
      [EnumShortParams.DATA_COVERAGE]: this.filter.dataCoverage.isActive
        ? this.dataCoverage.map(n => n.toString()) || undefined
        : undefined,
      [EnumShortParams.SORT]:
        (this.searchQuery ? this.sort : this.sortEmpty) || undefined,
    }
  }

  created() {
    this._loadRouteParams()
    this._onSearch()
  }

  public onIntersect(_isIntersecting: boolean, entries: any[], _observer: any) {
    this.isIntersecting = entries[0]?.intersectionRatio >= 0.5
    if (
      this.isIntersecting
      && this.results.length
      && this.hasMore
      && !this.isSearching
      && !this.isFetchingMore
    ) {
      this.fetchMore()
    }
  }

  /** Pushes the desired search to the router, which will reload the route with the new query parameters */
  pushSearchRoute() {
    try {
      if (this.queryParams.term) {
        SearchHistory.log(this.queryParams.term)
      }

      // This will reload the component because the router-view in the App component has `:key="route.fullPath"`
      this.router
        .push({
          name: 'search',
          query: this.routeParams,
        })
        .catch(sameRouteNavigationErrorHandler)
    }
    catch (e) {
      console.log(e)
      Search.commit((state) => {
        state.results = []
      })
      Notifications.toast({
        message: `Failed to perform search`,
        type: 'error',
      })
    }
  }

  async _onSearch() {
    this.hasMore = true
    this.isSearching = true
    this.pageNumber = 1

    this.hasMore = await Search.search(this.queryParams)
    this.isSearching = false
  }

  /** Get the next page of results. */
  public async fetchMore() {
    this.pageNumber++
    this.isFetchingMore = true
    try {
      this.hasMore = await Search.fetchMore(this.queryParams)
    }
    catch (e) {
      console.log(e)
    }
    this.isFetchingMore = false
  }

  public onSliderControlChange(filter: {
    min: number
    max: number
    isActive: boolean
  }) {
    filter.isActive = true

    this.pushSearchRoute()
  }

  public highlightCreators(result: IResult) {
    if (!result.creator) {
      return ''
    }
    const div = document.createElement('DIV')
    // div.innerHTML = result.creator.join(", ");
    div.innerHTML = result.creator[0]

    let content = div.textContent || div.innerText || ''

    if (result.highlights) {
      let hits = result.highlights
        .filter(highlight => highlight.path === 'creator.@list.name')
        .map(hit =>
          hit.texts.filter(t => t.type === 'hit').map(t => t.value),
        )
        .flat()

      hits = [...new Set(hits)]
      hits.map((hit) => {
        content = content.replaceAll(hit, `<mark>${hit}</mark>`)
      })
    }

    return content
  }

  /** Applies highlights to a string or string[] field and returns the new content as HTML */
  public highlight(result: IResult, path: keyof IResult) {
    const div = document.createElement('DIV')
    const field = result[path]

    div.innerHTML = Array.isArray(field) ? field.join(', ') : field
    let content = div.textContent || div.innerText || ''

    if (result.highlights) {
      let hits = result.highlights
        .filter(highlight => highlight.path === path)
        .map(hit =>
          hit.texts.filter(t => t.type === 'hit').map(t => t.value),
        )
        .flat()

      hits = [...new Set(hits)]
      hits.map((hit) => {
        content = content.replaceAll(hit, `<mark>${hit}</mark>`)
      })
    }

    return content
  }

  public clearFilters() {
    const wasSomeActive = this.isSomeFilterActive

    this.filter.creationDate.isActive = false
    this.creationDate = [MIN_YEAR, MAX_YEAR]

    this.filter.publicationYear.isActive = false
    this.publicationYear = [MIN_YEAR, MAX_YEAR]

    this.filter.dataCoverage.isActive = false
    this.dataCoverage = [MIN_YEAR, MAX_YEAR]

    this.filter.availability.value = null
    this.filter.availability.isActive = false

    this.filter.contentType.value = null
    this.filter.contentType.isActive = false

    this.filter.authorName = ''
    this.filter.contributorName = ''
    this.filter.ownerName = ''
    this.filter.subject = ''
    this.filter.funder = ''

    if (wasSomeActive) {
      this.pushSearchRoute()
    }
  }

  /** Load route query parameters into component values. */
  private _loadRouteParams() {
    // SEARCH QUERY
    this.searchQuery = this.$route.query.q as string

    this.filter.authorName
      = (this.$route.query[EnumShortParams.AUTHOR_NAME] as string) || ''
    this.filter.contributorName
      = (this.$route.query[EnumShortParams.CONTRIBUTOR_NAME] as string) || ''
    this.filter.ownerName
      = (this.$route.query[EnumShortParams.OWNER_NAME] as string) || ''
    this.filter.funder
      = (this.$route.query[EnumShortParams.FUNDER] as string) || ''
    this.filter.subject
      = (this.$route.query[EnumShortParams.SUBJECT] as string) || ''

    // CONTENT TYPE
    if (this.$route.query[EnumShortParams.CONTENT_TYPE]) {
      this.filter.contentType.isActive = true
      this.filter.contentType.value = this.$route.query[
        EnumShortParams.CONTENT_TYPE
      ]
        ? ([this.$route.query[EnumShortParams.CONTENT_TYPE]].flat() as string[])
        : null
    }

    // AVAILABILITY
    if (this.$route.query[EnumShortParams.AVAILABILITY]) {
      this.filter.availability.isActive = true
      this.filter.availability.value = this.$route.query[
        EnumShortParams.AVAILABILITY
      ]
        ? ([this.$route.query[EnumShortParams.AVAILABILITY]].flat() as string[])
        : null
    }

    // CREATION DATE
    if (this.$route.query[EnumShortParams.CREATION_DATE]) {
      this.filter.creationDate.isActive = true
      this.creationDate
        = ((
          this.$route.query[EnumShortParams.CREATION_DATE] as [string, string]
        )?.map(n => +n) as [number, number]) || this.creationDate
    }

    // PUBLICATION YEAR
    if (this.$route.query[EnumShortParams.PUBLICATION_YEAR]) {
      this.filter.publicationYear.isActive = true
      this.publicationYear
        = ((
          this.$route.query[EnumShortParams.PUBLICATION_YEAR] as [
            string,
            string,
          ]
        )?.map(n => +n) as [number, number]) || this.publicationYear
    }

    // DATA COVERAGE
    if (this.$route.query[EnumShortParams.DATA_COVERAGE]) {
      this.filter.dataCoverage.isActive = true
      this.dataCoverage
        = ((
          this.$route.query[EnumShortParams.DATA_COVERAGE] as [string, string]
        )?.map(n => +n) as [number, number]) || this.dataCoverage
    }

    // SORT
    if (this.route.query[EnumShortParams.SORT]) {
      if (this.searchQuery) {
        this.sort
          = (this.route.query[EnumShortParams.SORT] as
          | 'name'
          | 'dateCreated'
          | 'relevance') || this.sort
      }
      else {
        this.sortEmpty
          = (this.route.query[EnumShortParams.SORT] as
          | 'name'
          | 'dateCreated'
          | 'relevance') || this.sort
      }
    }
  }

  public hasSpatialFeatures(result: IResult): boolean {
    return result.spatialCoverage
  }
}
export default toNative(CdSearchResults)
</script>

<template>
  <v-container
    class="cd-search-results text-body-1"
    :class="{ 'is-small': $vuetify.display.smAndDown }"
  >
    <div class="d-flex align-baseline">
      <div class="text-h5 font-weight-bold mr-2">
        Discover
      </div>
      <div class="text-medium-emphasis text-body-1 font-italic">
        Public resources shared with the community
      </div>
    </div>
    <v-divider class="mt-2 mb-6" />
    <div class="d-sm-block d-md-flex">
      <v-container class="sidebar flex-shrink-0">
        <div class="sidebar--content">
          <div class="text-h6 mb-6">
            Filters
          </div>

          <v-expansion-panels v-model="panels" multiple>
            <v-expansion-panel key="0" tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-3">
                <v-switch
                  v-model="filter.availability.isActive"
                  density="compact"
                  hide-details
                  color="primary"
                  @click.stop=""
                  @update:model-value="pushSearchRoute"
                />
                <div class="ml-4 text-body-1 cursor-pointer">
                  Availiability
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <div
                  v-for="(option, index) of filter.availability.options"
                  class="d-flex justify-space-between align-center"
                >
                  <v-checkbox
                    :key="index"
                    v-model="filter.availability.value"
                    :label="option"
                    :value="option"
                    hide-details
                    density="compact"
                    @update:model-value="pushSearchRoute"
                  />
                  <v-icon v-bind="availabilityIcons[index]">
                    {{
                      availabilityIcons[index].icon
                    }}
                  </v-icon>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel key="1" tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-3">
                <v-switch
                  v-model="filter.contentType.isActive"
                  density="compact"
                  hide-details
                  color="primary"
                  @click.stop=""
                  @update:model-value="pushSearchRoute"
                />
                <div class="ml-4 text-body-1 cursor-pointer">
                  Content type
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <v-checkbox
                  v-for="(option, index) of filter.contentType.options"
                  :key="index"
                  v-model="filter.contentType.value"
                  :label="option"
                  :value="option"
                  hide-details
                  density="compact"
                  color="primary"
                  @update:model-value="pushSearchRoute"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel key="2" tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
                <v-switch
                  v-model="filter.dataCoverage.isActive"
                  density="compact"
                  hide-details
                  color="primary"
                  @click.stop=""
                  @update:model-value="pushSearchRoute"
                />
                <div class="ml-4 text-body-1 cursor-pointer">
                  Temporal coverage
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <cd-range-input
                  v-model="dataCoverage"
                  v-model:is-active="filter.dataCoverage.isActive"
                  :min="filter.dataCoverage.min"
                  :max="filter.dataCoverage.max"
                  label="Temporal coverage"
                  @update:is-active="pushSearchRoute"
                  @end="onSliderControlChange(filter.dataCoverage)"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel key="3" tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
                <v-switch
                  v-model="filter.creationDate.isActive"
                  density="compact"
                  hide-details
                  color="primary"
                  @click.stop=""
                  @update:model-value="pushSearchRoute"
                />

                <div class="ml-4 text-body-1 cursor-pointer">
                  Date created
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text key="4">
                <!-- DATA COVERAGE -->
                <cd-range-input
                  v-model="creationDate"
                  v-model:is-active="filter.creationDate.isActive"
                  :min="filter.creationDate.min"
                  :max="filter.creationDate.max"
                  label="Date created"
                  @update:is-active="pushSearchRoute"
                  @end="onSliderControlChange(filter.creationDate)"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
                <v-switch
                  v-model="filter.publicationYear.isActive"
                  density="compact"
                  hide-details
                  color="primary"
                  @click.stop=""
                  @update:model-value="pushSearchRoute"
                />

                <div class="ml-4 text-body-1 cursor-pointer">
                  Publication year
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <!-- PUBLICATION YEAR -->
                <cd-range-input
                  v-model="publicationYear"
                  v-model:is-active="filter.publicationYear.isActive"
                  :min="filter.publicationYear.min"
                  :max="filter.publicationYear.max"
                  label="Publication year"
                  @update:is-active="pushSearchRoute"
                  @end="onSliderControlChange(filter.publicationYear)"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <!-- AUTHOR NAME -->
          <v-text-field
            v-model="filter.authorName"
            label="Author's name"
            class="mt-6"
            prepend-inner-icon="mdi-account-edit"
            hide-details
            clearable
            variant="outlined"
            @blur="pushSearchRoute"
            density="compact"
            @keyup.enter="pushSearchRoute"
            @click:clear="pushSearchRoute"
          />

          <v-text-field
            v-model="filter.ownerName"
            label="Owner's name"
            class="mt-6"
            prepend-inner-icon="mdi-account-key"
            hide-details
            clearable
            variant="outlined"
            @blur="pushSearchRoute"
            density="compact"
            @keyup.enter="pushSearchRoute"
            @click:clear="pushSearchRoute"
          />

          <v-text-field
            v-model="filter.contributorName"
            label="Contributor's name"
            class="mt-6"
            prepend-inner-icon="mdi-account-group"
            hide-details
            clearable
            variant="outlined"
            @blur="pushSearchRoute"
            density="compact"
            @keyup.enter="pushSearchRoute"
            @click:clear="pushSearchRoute"
          />

          <v-text-field
            v-model="filter.subject"
            label="Subject"
            class="mt-6"
            prepend-inner-icon="mdi-pen"
            hide-details
            clearable
            variant="outlined"
            @blur="pushSearchRoute"
            density="compact"
            @keyup.enter="pushSearchRoute"
            @click:clear="pushSearchRoute"
          />

          <v-text-field
            v-model="filter.funder"
            label="Funder"
            class="mt-6"
            prepend-inner-icon="mdi-domain"
            hide-details
            clearable
            variant="outlined"
            @blur="pushSearchRoute"
            density="compact"
            @keyup.enter="pushSearchRoute"
            @click:clear="pushSearchRoute"
          />

          <!-- <div class="text-center mt-8">
            <v-btn
              @click="clearFilters"
              :disabled="!isSomeFilterActive"
              variant="text"
              >Clear Filters</v-btn
            >
          </div> -->
        </div>
      </v-container>

      <div class="results-content-wrapper">
        <v-container class="results-content">
          <div class="d-flex align-center gap-1 mb-6">
            <cd-search
              v-model="searchQuery"
              :input-attrs="{ variant: 'outlined' }"
              @update:model-value="pushSearchRoute"
              @clear="
                searchQuery = '';
                pushSearchRoute();
              "
            />
            <v-card
              v-if="isSomeFilterActive"
              density="compact"
              flat
              variant="outlined"
            >
              <v-card-text class="d-flex align-center py-2">
                <div class="text-body-2 mr-1">
                  Active filters
                </div>
                <v-btn
                  variant="text"
                  density="compact"
                  icon="mdi-close"
                  size="small"
                  title="Clear filters"
                  @click="clearFilters"
                />
              </v-card-text>
            </v-card>
          </div>

          <div class="results-container mb-12">
            <template v-if="isSearching">
              <!-- TODO: refactor into a component -->
              <v-skeleton-loader type="list-item" width="150" />
              <v-card elevation="2">
                <v-card-text>
                  <div v-for="index in 4" :key="index">
                    <v-skeleton-loader type="table-tbody" />
                  </div>
                </v-card-text>
              </v-card>
            </template>
            <template v-else-if="false">
              <v-card
                v-if="!results.length"
                class="text-body-2 text-center mt-8"
              >
                <v-empty-state
                  text="No results found."
                  icon="mdi-text-box-remove"
                />
              </v-card>
              <div
                v-if="searchResultsMetadata?.count?.total"
                class="text-body-1 text-medium-emphasis mb-4"
              >
                {{ searchResultsMetadata?.count?.total || "" }} result{{
                  searchResultsMetadata?.count?.total != 1 ? "s" : ""
                }}
              </div>
              <div
                v-for="result of results"
                :key="result.id"
                class="mb-16 text-body-2"
              >
                <a
                  class="text-h6 text-decoration-none my-12"
                  :href="result.url"
                  target="_blank"
                  v-html="highlight(result, 'name')"
                />
                <div class="my-1" v-html="highlightCreators(result)" />
                <div v-if="result.dateCreated" class="my-1">
                  Date Created: {{ formatDate(result.dateCreated) }}
                </div>
                <div v-if="result.datePublished" class="my-1">
                  Publication Date: {{ formatDate(result.datePublished) }}
                </div>
                <p
                  class="mt-4 mb-1"
                  :class="{ 'snip-3': !result._showMore }"
                  v-html="highlight(result, 'description')"
                />

                <v-btn
                  size="x-small"
                  variant="text"
                  color="primary"
                  @click="result._showMore = !result._showMore"
                >
                  Show {{ result._showMore ? "less" : "more" }}...
                </v-btn>

                <div
                  class="d-flex gap-1 justify-space-between flex-wrap flex-lg-nowrap mt-2"
                >
                  <div>
                    <a
                      class="mb-2 d-block"
                      :href="result.url"
                      target="_blank"
                    >{{ result.url }}</a>
                    <div class="mb-2">
                      <strong>Keywords: </strong><span v-html="highlight(result, 'keywords')" />
                    </div>
                    <div v-if="result.funding.length" class="mb-2">
                      <strong>Funded by: </strong>{{ result.funding.join(", ") }}
                    </div>
                    <div v-if="result.license" class="mb-2">
                      <strong>License: </strong>{{ result.license }}
                    </div>
                  </div>

                  <div
                    v-if="hasSpatialFeatures(result)"
                    :id="`map-${result.id}`"
                  >
                    <cd-spatial-coverage-map
                      :loader="loader"
                      :loader-options="options"
                      :feature="result.spatialCoverage"
                    />
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <v-card
                v-if="!results.length"
                elevation="2"
                class="text-body-2 text-center mt-8 py-12"
              >
                <v-card-text>
                  <v-empty-state
                    text="No results found."
                    icon="mdi-text-box-remove"
                  />
                </v-card-text>
              </v-card>
              <div
                v-if="searchResultsMetadata?.count?.total"
                class="text-body-1 text-medium-emphasis mb-4"
              >
                {{ searchResultsMetadata?.count?.total || "" }} result{{
                  searchResultsMetadata?.count?.total != 1 ? "s" : ""
                }}
              </div>

              <v-data-table-virtual
                v-if="results.length"
                :headers="headers.filter((header) => header.visible)"
                :items="results"
                class="elevation-2 text-body-1"
                hover
                expand-on-click
                show-expand
              >
                <!-- <template v-slot:item.icons="{ item }"></template> -->
                <template #item.title="{ item }">
                  <a
                    class="text-decoration-none"
                    :href="item.url"
                    target="_blank"
                    v-html="highlight(item, 'name')"
                  />
                </template>
                <template #item.firstAuthor="{ item }">
                  <div v-html="highlightCreators(item)" />
                </template>
                <template #item.dateCreated="{ item }">
                  <span v-if="item.dateCreated">{{
                    formatDate(item.dateCreated)
                  }}</span>
                </template>
                <template #item.lastModified="{ item }">
                  <span v-if="item.lastModified">{{
                    formatDate(item.lastModified)
                  }}</span>
                </template>
                <template #expanded-row="{ item }">
                  <div class="d-table-row">
                    <td class="d-table-cell" colspan="6">
                      <v-card class="mx-4" flat>
                        <v-card-text>
                          <div class="d-flex gap-2">
                            <div class="flex-grow-1">
                              <div class="text-h6">
                                Subject Keywords
                              </div>
                              <div>
                                <v-chip
                                  v-for="keyword of item.keywords"
                                  size="small"
                                  style="margin: 0.25rem"
                                >
                                  {{ keyword }}
                                </v-chip>
                              </div>
                              <div class="text-h6 mt-4">
                                Abstract
                              </div>
                              <p
                                :class="{ 'snip-3': !item._showMore }"
                                v-html="highlight(item, 'description')"
                              />

                              <v-btn
                                size="x-small"
                                variant="text"
                                color="primary"
                                @click="item._showMore = !item._showMore"
                              >
                                Show
                                {{ item._showMore ? "less" : "more" }}...
                              </v-btn>
                            </div>

                            <div v-if="hasSpatialFeatures(item)">
                              <div class="text-h6">
                                Spatial Coverage
                              </div>

                              <div :id="`map-${item.id}`" class="mb-4">
                                <cd-spatial-coverage-map
                                  :loader="loader"
                                  :loader-options="options"
                                  :feature="item.spatialCoverage"
                                />
                              </div>
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                      <v-divider />
                    </td>
                  </div>
                </template>

                <!-- <div class="my-1" v-if="result.datePublished">
                  Publication Date: {{ formatDate(result.datePublished) }}
                </div> -->
              </v-data-table-virtual>
            </template>
          </div>

          <div
            v-if="results.length"
            v-intersect="{
              handler: onIntersect,
              options: { threshold: [0, 0.5, 1.0] },
            }"
          />
          <div v-if="isFetchingMore" class="text-subtitle-2 text-center">
            Loading more results...
          </div>
          <div
            v-if="results.length && !hasMore"
            class="text-subtitle-2 text-center"
          >
            End of results.
          </div>
        </v-container>
      </div>
    </div>
  </v-container>
</template>

<style lang="scss" scoped>
.v-expansion-panel--active,
.v-expansion-panel--active:not(:first-child),
.v-expansion-panel--active + .v-expansion-panel {
  margin-top: 1px;
}

:deep(.v-table .v-data-table__tr:nth-child(even) td) {
  background: #f7f7f7;
}

:deep(.v-table tr.v-data-table__tr td) {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.sidebar {
  width: 20rem;
}

.cd-search-results.is-small {
  .sidebar {
    width: 100%;
  }
}

.results-content-wrapper {
  flex: 1 1 auto;
}

// .results-content {
//   min-width: 0; // https://stackoverflow.com/a/66689926/3288102
//   max-width: 70rem;
//   margin: unset;
// }

.results-container {
  * {
    word-break: break-word;
  }

  a {
    text-decoration: none;
    &:hover {
      text-decoration: underline !important;
    }
  }
}

.grayed-out {
  opacity: 0.55;
}

:deep(.v-select--chips .v-select__selections .v-chip--select:first-child) {
  margin-top: 1rem;
}
</style>
