FROM node:23 as build-stage
ARG VITE_APP_BASE
ARG VITE_APP_API_URL
ARG VITE_APP_NAME
WORKDIR /app
COPY ./frontend/ .
RUN npm install
RUN npm run build-prod

FROM nginx:1.23.1 as production-stage
RUN mkdir /app
COPY --from=build-stage /app/dist /app
COPY --from=build-stage /app/nginx.conf /etc/nginx/nginx.conf
EXPOSE 5003
