FROM nginx:alpine

COPY arcade-bar-south.html /usr/share/nginx/html/index.html

EXPOSE 80
