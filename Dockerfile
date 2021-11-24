FROM python:3.4-alpine3.8
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code

RUN adduser -D -u 1000 nginx

## Install dependencies

RUN apk --update add --no-cache postgresql-dev nginx supervisor gettext build-base jpeg-dev zlib-dev libffi-dev
RUN rm -rf /var/cache/apk/*

## Install requirements
ADD django/requirements.txt /code/
RUN pip install -r requirements.txt

## Install webserver
RUN pip install gunicorn
ADD tools/webserver/supervisor-prod.ini /etc/supervisor.d/supervisor.ini.prod
ADD tools/webserver/supervisor-dev.ini /etc/supervisor.d/supervisor.ini.dev

RUN mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
ADD tools/webserver/rially-dev.conf /etc/nginx/nginx.conf.dev
ADD tools/webserver/rially-prod.conf /etc/nginx/nginx.conf.prod
RUN mkdir /run/nginx/


## Timezone
RUN apk add --no-cache tzdata
RUN cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime
RUN echo 'Europe/Amsterdam' > /etc/timezone
RUN apk del tzdata

ADD django/. /code/
RUN chmod +x /code/entrypoint.sh

RUN mkdir /var/www/media
ADD media/. /var/www/media
RUN chown -R nginx /var/www/media

EXPOSE 80
EXPOSE 443
ENTRYPOINT ["/code/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisord.conf"]
