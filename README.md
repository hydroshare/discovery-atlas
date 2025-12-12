# Archived on December 12th 2025

## This repository has been integrated into https://github.com/hydroshare/hydroshare

[https://github.com/hydroshare/hydroshare/commit/1df83f59897eae71f9e13ccfb887a3c4814bd9cf](https://github.com/hydroshare/hydroshare/commit/1df83f59897eae71f9e13ccfb887a3c4814bd9cf)


# HydroShare Discovery Portal with Atlas

## Getting Started

### Clone the repo, checkout this branch
```console
git clone https://github.com/hydroshare/discover-atlas.git
```

### API for local development
```console
cp .env.template .env
# modify settings as necessary in the .env (at least MONGO_URL and MONGO_DATABASE)
make build
make up
```
The root route of the API will be available at http://localhost:8000. 
The swagger docs will be at http://localhost:8000/docs. 
The Redoc is at http://localhost:8000/redoc. 

### Frontend for local development
```console
cp .env.template .env  #if you haven't already
cd frontend
npm install
npm run serve
```
The frontend will be available at http://localhost:5003/
More detailed info is available in the [frontend readme](frontend/README.md)

## Formatting
```console
make format
```
