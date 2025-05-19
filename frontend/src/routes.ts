import type { RouteRecordRaw } from 'vue-router'
import AuthRedirect from '@/components/account/auth-redirect.vue'
import CdFooter from '@/components/base/cd.footer.vue'
import CdSearchResults from '@/components/search-results/cd.search-results.vue'

export const routes: RouteRecordRaw[] = [
  {
    name: 'search',
    path: '/',
    components: {
      content: CdSearchResults,
      footer: CdFooter,
    },
    meta: {
      title: 'Search',
    },
  },
  {
    name: 'auth-redirect',
    path: '/auth-redirect',
    components: {
      content: AuthRedirect,
    },
    meta: {
      hideNavigation: true,
    },
  },
  /** @see https://router.vuejs.org/guide/migration/#removed-star-or-catch-all-routes */
  { path: '/:pathMatch(.*)*', name: 'not-found', redirect: { name: 'search' } },
  {
    path: '/:pathMatch(.*)',
    name: 'bad-not-found',
    redirect: { name: 'search' },
  },
]
