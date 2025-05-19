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
The frontend will be available at http://localhost:8080/
More detailed info is available in the [frontend readme](frontend/README.md)

## Formatting
```console
make format
```
Formatting and linting is run with a git pre-commit hook using Husky.
It requires the Docker daemon to be running.
If you are having trouble with the formatting and linting, you can see here how to skip the git hook:
https://typicode.github.io/husky/how-to.html#skipping-git-hooks
However note that this is not recommended -- let's keep our code clean!
