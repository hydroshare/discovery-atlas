import SearchHistory from './search-history.model'
import SearchResults from './search-results.model'
import User from './user.model'

export const persistedPaths = [
  `entities.${User.entity}`,
  `entities.${SearchResults.entity}.sort`,
  `entities.${SearchHistory.entity}`,

  `entities.${SearchResults.entity}.publicationYear`,
  `entities.${SearchResults.entity}.dataCoverage`,
  `entities.${SearchResults.entity}.creationDate`,
  `entities.${SearchResults.entity}.panels`,
]
