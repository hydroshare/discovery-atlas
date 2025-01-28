# HydroShare Discovery Portal with Atlas

## Getting Started

### Clone the repo, checkout this branch
```console
git clone https://github.com/hydroshare/discover-atlas.git
```

### API for local development
```console
cd app
cp .env.template .env
make build
make up
```
The API will be available at http://0.0.0.0:8000

### Frontend for local development
```console
cd app
cp .env.template .env  #if you haven't already
cd frontend
npm install
npm run dev
```
The frontend will be available at http://localhost:5173/discover
More detailed info is available in the [frontend readme](frontend/README.md)

## Formatting
```console
make format
```
