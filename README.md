This script sets up a Let's Encrypt certificate on an Nginx webserver for use in a Docker environment. It only takes a minute.

## tl;dr - how to install

- Ensure your DNS is already configured and propagated.
- Copy the `certbot.py` and `certbot.json` files from this repo to your server.
  ```
  curl -OO https://raw.githubusercontent.com/joncombe/docker-nginx-letsencrypt-setup/main/{certbot.json,certbot.py}
  ```
- Edit `certbot.json` to taste. You likely only need to edit `domain` and `email`.
- Run the script:
  ```
  python3 certbot.py
  ```
- Add the following line to your crontab so that certificates automatically renew:
  ```
  0 0,12 * * * docker compose run --rm certbot renew
  ```

## The background

There is an _excellent_ blog post on this topic, [HTTPS using Nginx and Let's encrypt in Docker](https://mindsers.blog/post/https-using-nginx-certbot-docker/), which has helped me many times (_thank you, Nathanaël_). This script goes through very similar steps to what is described in that blog post, but in an automated way.

This has been tested on Ubuntu servers. I think it will work on any Linux environment with Docker installed but I'd appreciate your feedback on that.

## What it does

1. It creates a `docker-compose.yml` with `nginx` and `certbot` containers.
1. It creates a temporary `nginx.conf` file with enough configuration for certbot to do it's magic.
1. It fetches the certificates from Let's Encrypt.
1. It creates a new copy of `nginx.conf` with all the settings you need to serve your website using SSL, and also redirect non-SSL traffic to the SSL version.
1. It leaves you with two files you can edit to suit your project:
   - `docker-compose.yml`: Be careful not to remove any of the 3 lines in the `volumes` section. Add as many other lines as you like, but keep the ones generated for you here intact.
   - `nginx.conf`: You probably don't need to touch the port 80 section at all (the `location /.well-known/acme-challenge/` section must remain so the certificates can renew). You can edit the port 443 section as you like but don't touch the `ssl_certificate` and `ssl_certificate_key` lines.

## Configuration

```
{
  "domain": "example.com",
  "email": "certbot@example.com",
  "nginx_image": "nginx:1.23.2-alpine",
  "volume_prefix": "./data"
}
```

- `domain` should be the FQDN of your website, e.g. _en.wikipedia.org_
- `email` is the email address you provide to Let's Encrypt
- `nginx_image` is the name of the nginx image to use. Leaving it the default value will be fine for most of you.
- `volume_prefix` is the local path to the location your persisted docker data files are stored. If you are not sure what to do here, leave it as it is. _[TODO: improve how to explain this, my terminology has failed me]_

## Example output

docker-compose.yml

```
version: '3'

services:
  webserver:
    image: nginx:1.23.2-alpine
    ports:
      - 80:80
      - 443:443
    restart: always
    volumes:
      - ./data/certbot/conf/:/etc/nginx/ssl/:ro
      - ./data/certbot/www:/var/www/certbot/:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro

  certbot:
    image: certbot/certbot:latest
    volumes:
      - ./data/certbot/conf/:/etc/letsencrypt/:rw
      - ./data/certbot/www/:/var/www/certbot/:rw

```

nginx.conf

```
server {{
    listen 80;
    listen [::]:80;

    server_name _;
    server_tokens off;

    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}

    location / {{
        return 301 https://example.com$request_uri;
    }}
}}

server {{
    listen 443 default_server ssl http2;
    listen [::]:443 ssl http2;

    server_name _;
    server_tokens off;

    ssl_certificate /etc/nginx/ssl/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/example.com/privkey.pem;

    location / {{
        if ( $host !~* ^(example.com)$ ) {{
            return 444;
        }}

        # you will likely want to replace the following line with
        # your own configuration
        root /usr/share/nginx/html;
    }}
}}
```

## Legal

Be aware, running this next command assumes you agree to the Let's Encrypt Terms of Service. See: https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf. If you do not agree to these rules, please do NOT use this script.
