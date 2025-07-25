import json
import mimetypes
from datetime import datetime
from typing import Optional
import functools

from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from config import get_settings

router = APIRouter()


class SearchQuery(BaseModel):
    term: Optional[str] = None
    sortBy: Optional[str] = None
    order: Optional[str] = None
    contentType: Optional[list[str]] = []
    providerName: Optional[str] = None
    creatorName: Optional[str] = None
    contributorName: Optional[str] = None
    keyword: Optional[str] = None
    dataCoverageStart: Optional[int] = None
    dataCoverageEnd: Optional[int] = None
    publishedStart: Optional[int] = None
    publishedEnd: Optional[int] = None
    dateCreatedStart: Optional[int] = None
    dateCreatedEnd: Optional[int] = None
    dateModifiedStart: Optional[int] = None
    dateModifiedEnd: Optional[int] = None
    hasPartName: Optional[str] = None
    isPartOfName: Optional[str] = None
    associatedMediaName: Optional[str] = None
    fundingGrantName: Optional[str] = None
    fundingFunderName: Optional[str] = None
    creativeWorkStatus: Optional[list[str]] = []
    pageNumber: int = 1
    pageSize: int = 20
    paginationToken: Optional[str]

    @field_validator('*')
    def empty_str_to_none(cls, v, info: ValidationInfo):
        if info.field_name == 'term' and v:
            return v.strip()

        # Don't convert empty strings to None for list fields like contentType/creativeWorkStatus
        if info.field_name in ['contentType', 'creativeWorkStatus']:
            return v

        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    @field_validator('contentType', 'creativeWorkStatus')
    def validate_list_type_fields(cls, v):
        """Ensure contentType/creativeWorkStatus is always a list and filter out empty strings"""
        if v is None:
            return []
        if isinstance(v, str):
            # Handle single string values
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            # Filter out empty strings from list
            return [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return []

    @field_validator('dataCoverageStart', 'dataCoverageEnd', 'publishedStart', 'publishedEnd', 'dateCreatedStart', 'dateCreatedEnd', 'dateModifiedStart', 'dateModifiedEnd')
    def validate_year(cls, v, info: ValidationInfo):
        if v is None:
            return v
        try:
            datetime(v, 1, 1)
        except ValueError:
            raise ValueError(f'{info.field_name} is not a valid year')

        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.dataCoverageStart and self.dataCoverageEnd and self.dataCoverageEnd < self.dataCoverageStart:
            raise ValueError('dataCoverageEnd must be greater or equal to dataCoverageStart')
        if self.publishedStart and self.publishedEnd and self.publishedEnd < self.publishedStart:
            raise ValueError('publishedEnd must be greater or equal to publishedStart')
        if self.dateCreatedStart and self.dateCreatedEnd and self.dateCreatedEnd < self.dateCreatedStart:
            raise ValueError('dateCreatedEnd must be greater or equal to dateCreatedStart')
        if self.dateModifiedStart and self.dateModifiedEnd and self.dateModifiedEnd < self.dateModifiedStart:
            raise ValueError('dateModifiedEnd must be greater or equal to dateModifiedStart')

    @field_validator('pageNumber', 'pageSize')
    def validate_page(cls, v, info: ValidationInfo):
        if v <= 0:
            raise ValueError(f'{info.field_name} must be greater than 0')
        return v

    @property
    def _filters(self):
        filters = []

        # filter out aggregation type documents - aggregation types do not have a value for dateCreated
        filters.append({'compound': {'mustNot': [{'equals': {'path': 'dateCreated', 'value': None}}]}})

        if self.publishedStart:
            filters.append(
                {
                    'range': {
                        'path': 'datePublished',
                        'gte': datetime(self.publishedStart, 1, 1),
                    },
                }
            )
        if self.publishedEnd:
            filters.append(
                {
                    'range': {
                        'path': 'datePublished',
                        'lt': datetime(self.publishedEnd + 1, 1, 1),  # +1 to include all of the publishedEnd year
                    },
                }
            )

        if self.dateCreatedStart:
            filters.append(
                {
                    'range': {
                        'path': 'dateCreated',
                        'gte': datetime(self.dateCreatedStart, 1, 1),
                    },
                }
            )
        if self.dateCreatedEnd:
            filters.append(
                {
                    'range': {
                        'path': 'dateCreated',
                        'lt': datetime(self.dateCreatedEnd + 1, 1, 1),  # +1 to include all of the dateCreatedEnd year
                    },
                }
            )

        if self.dateModifiedStart:
            filters.append(
                {
                    'range': {
                        'path': 'dateModified',
                        'gte': datetime(self.dateModifiedStart, 1, 1),
                    },
                }
            )
        if self.dateModifiedEnd:
            filters.append(
                {
                    'range': {
                        'path': 'dateModified',
                        'lt': datetime(self.dateModifiedEnd + 1, 1, 1),  # +1 to include all of the dateModifiedEnd year
                    },
                }
            )

        if self.dataCoverageStart:
            filters.append(
                {'range': {'path': 'temporalCoverage.startDate', 'gte': datetime(self.dataCoverageStart, 1, 1)}}
            )
        if self.dataCoverageEnd:
            filters.append(
                {'range': {'path': 'temporalCoverage.endDate', 'lt': datetime(self.dataCoverageEnd + 1, 1, 1)}}
            )

        filters.append({'term': {'path': 'type', 'query': "Dataset"}})

        return filters

    @property
    def _should(self):
        search_paths = ['name', 'description', 'keywords']
        should = [{'autocomplete': {'query': self.term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]
        return should

    @property
    def _must(self):
        must = []
        if self.contentType and len(self.contentType) > 0:
            # Use exact term matching for each content type to ensure precise filtering
            if len(self.contentType) == 1:
                # Single content type - use term for exact match
                must.append({'term': {'path': 'additionalType', 'query': self.contentType[0]}})
            else:
                # Multiple content types - use compound OR with exact term matches
                # This ensures each content type is matched exactly, not partially
                content_type_conditions = []
                for content_type in self.contentType:
                    content_type_conditions.append({'term': {'path': 'additionalType', 'query': content_type}})
                must.append({'compound': {'should': content_type_conditions}})
        if self.creatorName:
            must.append({'text': {'path': 'creator.name', 'query': self.creatorName}})
        if self.contributorName:
            must.append({'text': {'path': 'contributor.name', 'query': self.contributorName}})
        if self.keyword:
            must.append({'text': {'path': 'keywords', 'query': self.keyword}})
        if self.providerName:
            must.append({'text': {'path': 'provider.name', 'query': self.providerName}})
        if self.hasPartName:
            must.append({'text': {'path': 'hasPart.name', 'query': self.hasPartName}})
        if self.isPartOfName:
            must.append({'text': {'path': 'isPartOf.name', 'query': self.isPartOfName}})
        if self.associatedMediaName:
            must.append({'text': {'path': 'associatedMedia.name', 'query': self.associatedMediaName}})
        if self.fundingGrantName:
            must.append({'text': {'path': 'funding.name', 'query': self.fundingGrantName}})
        if self.fundingFunderName:
            must.append({'text': {'path': 'funding.funder.name', 'query': self.fundingFunderName}})
        if self.creativeWorkStatus and len(self.creativeWorkStatus) > 0:
            # Use exact term matching for each creative work status to ensure precise filtering
            if len(self.creativeWorkStatus) == 1:
                # Single creative work status - use term for exact match on both possible paths
                must.append({
                    'compound': {
                        'should': [
                            {'term': {'path': 'creativeWorkStatus', 'query': self.creativeWorkStatus[0]}},
                            {'term': {'path': 'creativeWorkStatus.name', 'query': self.creativeWorkStatus[0]}}
                        ]
                    }
                })
            else:
                # Multiple creative work statuses - use compound OR with exact term matches
                status_conditions = []
                for status in self.creativeWorkStatus:
                    status_conditions.append({
                        'compound': {
                            'should': [
                                {'term': {'path': 'creativeWorkStatus', 'query': status}},
                                {'term': {'path': 'creativeWorkStatus.name', 'query': status}}
                            ]
                        }
                    })
                must.append({'compound': {'should': status_conditions}})
        return must


    @property
    def stages(self):
        highlightPaths = ['name', 'description', 'keywords', 'creator.name']
        stages = []
        compound = {'filter': self._filters, 'must': self._must, 'should': []}

        # The term is searched for in name, description, keywords and creator name
        # TODO: should the term be searched for in all fields?
        if self.term:
            if not self.sortBy:
                # Only apply scoring/boosting when not sorting, since sorting overrides relevance scoring
                compound['should'] = [
                    # https://www.mongodb.com/docs/atlas/atlas-search/score/modify-score/#std-label-scoring-boost
                    {'autocomplete': {'query': self.term, 'path': 'name', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 5 } }}},
                    {'autocomplete': {'query': self.term, 'path': 'description', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 3 } }}},
                    {'autocomplete': {'query': self.term, 'path': 'keywords', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 3 } }}},
                    {'autocomplete': {'query': self.term, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 5 } }}},
                ]
            else:
                # When sorting, use simple autocomplete without scoring/boosting
                compound['should'] = [
                    {'autocomplete': {'query': self.term, 'path': 'name', 'fuzzy': {'maxEdits': 1}}},
                    {'autocomplete': {'query': self.term, 'path': 'description', 'fuzzy': {'maxEdits': 1}}},
                    {'autocomplete': {'query': self.term, 'path': 'keywords', 'fuzzy': {'maxEdits': 1}}},
                    {'autocomplete': {'query': self.term, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1}}},
                ]
        
        # Dedicated input filters boost the score further if matched.
        if self.creatorName:
            if not self.sortBy:
                compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 5 } }}})
            else:
                compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1}}})

        if self.contributorName:
            if not self.sortBy:
                compound['should'].append({'autocomplete': {'query': self.contributorName, 'path': 'contributor.name', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 5 } }}})
            else:
                compound['should'].append({'autocomplete': {'query': self.contributorName, 'path': 'contributor.name', 'fuzzy': {'maxEdits': 1}}})

        if self.keyword:
            if not self.sortBy:
                compound['should'].append( {'autocomplete': {'query': self.keyword, 'path': 'keywords', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 3 } }}})
            else:
                compound['should'].append( {'autocomplete': {'query': self.keyword, 'path': 'keywords', 'fuzzy': {'maxEdits': 1}}})

        if self.fundingFunderName:
            if not self.sortBy:
                compound['should'].append({'autocomplete': {'query': self.fundingFunderName, 'path': 'funding.funder.name', 'fuzzy': {'maxEdits': 1}, 'score': { "boost": { "value": 3 } }}})
            else:
                compound['should'].append({'autocomplete': {'query': self.fundingFunderName, 'path': 'funding.funder.name', 'fuzzy': {'maxEdits': 1}}})
        
        search_stage = {
            '$search': {
                'index': 'fuzzy_search',
                'compound': compound,
                'highlight': {'path': highlightPaths},
                "concurrent": True,
                "returnStoredSource": True
            }
        }

        if self.paginationToken:
            search_stage["$search"]['searchAfter'] = self.paginationToken

        order = 1 if self.order == "asc" else -1

        # These sorts can occur inside the $search stage - these should be fast
        if self.sortBy == "name":
            search_stage["$search"]['sort'] = {"name": order}
        elif self.sortBy == "dateCreated":
            search_stage["$search"]['sort'] = {"dateCreated": order}
        elif self.sortBy == "lastModified":
            search_stage["$search"]['sort'] = {"dateModified": order}

        stages.append(search_stage)

        set_stage = {'$set': {
            'highlights': {'$meta': 'searchHighlights'}
        }}

        # When sorting, assign uniform score of 1 since sorting overrides relevance scoring
        if self.sortBy:
            set_stage['$set']['score'] = 1
        else:
            set_stage['$set']['score'] = {'$meta': 'searchScore'}

        # Sorting using an index for an array item requires a $sort stage. https://www.mongodb.com/docs/atlas/atlas-search/sort/#sort-option-limitations
        # Important to sort before appending paginationToken
        if self.sortBy == "creatorName":
            # this sort is slow as this is not part of the search stage
            # we should add a field 'firstAuthor' to the metadata document and store the first author name there for sorting
            stages.append({"$sort": {"creator.0.name": order}})
        else:
            set_stage['$set']['paginationToken'] = { "$meta" : "searchSequenceToken" } # searchSequenceToken cannot be used with $sort stage

        stages.append(set_stage)

        # Only apply relevance score threshold when not sorting
        if not self.sortBy:
            if self.term or self.creatorName or self.contributorName or self.keyword or self.contributorName:
                stages.append({'$match': {'score': {'$gt': get_settings().search_relevance_score_threshold}}})
        return stages


def get_search_query(
    term: Optional[str] = None,
    sortBy: Optional[str] = None,
    order: Optional[str] = None,
    contentType: list[str] = Query(default=[]),
    providerName: Optional[str] = None,
    creatorName: Optional[str] = None,
    contributorName: Optional[str] = None,
    keyword: Optional[str] = None,
    dataCoverageStart: Optional[int] = None,
    dataCoverageEnd: Optional[int] = None,
    publishedStart: Optional[int] = None,
    publishedEnd: Optional[int] = None,
    dateCreatedStart: Optional[int] = None,
    dateCreatedEnd: Optional[int] = None,
    dateModifiedStart: Optional[int] = None,
    dateModifiedEnd: Optional[int] = None,
    hasPartName: Optional[str] = None,
    isPartOfName: Optional[str] = None,
    associatedMediaName: Optional[str] = None,
    fundingGrantName: Optional[str] = None,
    fundingFunderName: Optional[str] = None,
    creativeWorkStatus: list[str] = Query(default=[]),
    pageNumber: int = 1,
    pageSize: int = 20,
    paginationToken: Optional[str] = None
) -> SearchQuery:
    """Custom dependency to handle contentType/creativeWorkStatus as both single values and lists"""

    # Create SearchQuery instance with processed parameters
    return SearchQuery(
        term=term,
        sortBy=sortBy,
        order=order,
        contentType=contentType,
        providerName=providerName,
        creatorName=creatorName,
        contributorName=contributorName,
        keyword=keyword,
        dataCoverageStart=dataCoverageStart,
        dataCoverageEnd=dataCoverageEnd,
        publishedStart=publishedStart,
        publishedEnd=publishedEnd,
        dateCreatedStart=dateCreatedStart,
        dateCreatedEnd=dateCreatedEnd,
        dateModifiedStart=dateModifiedStart,
        dateModifiedEnd=dateModifiedEnd,
        hasPartName=hasPartName,
        isPartOfName=isPartOfName,
        associatedMediaName=associatedMediaName,
        fundingGrantName=fundingGrantName,
        fundingFunderName=fundingFunderName,
        creativeWorkStatus=creativeWorkStatus,
        pageNumber=pageNumber,
        pageSize=pageSize,
        paginationToken=paginationToken
    )


@router.get("/search")
async def search(request: Request, search_query: SearchQuery = Depends(get_search_query)):
    stages = search_query.stages
    if not search_query.paginationToken:
        stages.append({"$skip": (search_query.pageNumber - 1) * search_query.pageSize})   
    stages.append({"$limit": search_query.pageSize})
    stages.append({
        "$lookup": {
            "from": "discovery", "localField": "_id", "foreignField": "_id", "as": "document"
        }
    })
    result = await request.app.mongodb["discovery"].aggregate(stages).to_list(None)
    json_str = json.dumps(result, default=str)
    return json.loads(json_str)


@router.get("/typeahead")
async def typeahead(request: Request, term: str, field: str = "term"):
    search_paths = ['name', 'description', 'keywords', "creator.name"] # default
    
    if field == "creator":
        search_paths = ["creator.name"]
    elif field == "contributor":
        search_paths = ["contributor.name"]
    elif field == "subject":
        search_paths = ["keywords"]
    elif field == "funder":
        search_paths = ["funding.funder.name"]

    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]

    stages = [
        {
            '$search': {
                'index': 'fuzzy_search',
                'compound': {'should': should},
                'highlight': {'path': search_paths},
                "concurrent": True,
                "returnStoredSource": True
            }
        },
        {
            '$project': {
                'name': 1,
                'description': 1,
                'keywords': 1,
                'creator': 1,
                'contributor': 1,
                'funding': 1,
                'highlights': {'$meta': 'searchHighlights'},
                '_id': 0,
            }
        },
    ]
    stages.append({"$limit": 20})
    stages.append({
        "$lookup": {
            "from": "discovery", "localField": "_id", "foreignField": "_id", "as": "document"
        }
    })
    result = await request.app.mongodb["discovery"].aggregate(stages).to_list(None)
    return result


def to_associated_media(file):
    mime_type = mimetypes.guess_type(file.name)[0]
    extension = file.extension
    mime_type = mime_type if mime_type else extension
    size = 0
    return {
        "@type": "DataDownload",
        "name": file.name,
        "contentUrl": file.url,
        "contentSize": size,
        "sha256": file.checksum,
        "encodingFormat": mime_type,
    }


@router.get("/content-types")
async def content_types(request: Request) -> list[str]:
    existing_content_types = await request.app.db[get_settings().mongo_database]["discovery"].find().distinct('additionalType')
    return sorted(existing_content_types, key=functools.cmp_to_key(lambda c1, c2 : c1 < c2))