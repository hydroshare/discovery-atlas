import type { UserModule } from '@/types'
import { APP_NAME } from '@/constants'
import { orm } from '@/models/orm'
import { persistedPaths } from '@/models/persistedPaths'
import VuexORM from '@vuex-orm/core'
import { createStore } from 'vuex'
import createPersistedState from 'vuex-persistedstate'

export const install: UserModule = ({ app }) => {
  // Create Vuex Store and register database through Vuex ORM.

  const store = createStore({
    plugins: [
      VuexORM.install(orm),
      createPersistedState({
        paths: persistedPaths,
        key: APP_NAME || 'HydroShare catalog',
      }),
    ],
    // state() {
    //   return {
    //     count: 0,
    //   }
    // },
    // mutations: {
    //   increment(state) {
    //     state.count++
    //   },
    // },
  })

  // Install the store instance as a plugin
  app.use(store)
}
