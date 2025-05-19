import type { UserModule } from '@/types'
import timeago from 'vue-timeago3'

export const install: UserModule = ({ app }) => {
  app.use(timeago)
}
