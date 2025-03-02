This script sets up a Let's Encrypt certificate on an Nginx webserver for use in a Docker environment. It only takes a minute.

You can read more about it here: https://www.joncom.be/projects/docker-nginx-letsencrypt-setup/

## How to use

- Ensure your DNS is already configured and propagated.
- Ensure docker and docker compose are installed on your server.
- Run the following line to copy the `certbot.py` and `certbot.json` files from this repo to your server.
  ```
  curl -OO https://raw.githubusercontent.com/joncombe/docker-nginx-letsencrypt-setup/main/{certbot.json,certbot.py}
  ```
- Edit `certbot.json`. You likely only need to edit the `domain` and `email` values.
- Run the script:
  ```
  python3 certbot.py
  ```
- Add the following lines to your crontab so that certificates automatically renew:
  ```
  0 0,12 * * *   docker compose run --rm certbot renew
  5 0 * * *      docker exec webserver nginx -s reload
  ```
- All done. Wasn't that easy?

## The background

There is an _excellent_ blog post on this topic, [HTTPS using Nginx and Let's Encrypt in Docker](https://mindsers.blog/post/https-using-nginx-certbot-docker/), which has helped me many times (_thank you, Nathanaël_). This script goes through very similar steps to what is described in that blog post but in an automated way.

This has been tested on Ubuntu servers. I think it will work on any Linux environment with Docker installed but I'd appreciate your feedback on that.

## What it does

1. It creates a `docker-compose.yml` with `nginx` and `certbot` containers.
1. It creates a temporary `nginx.conf` file with enough configuration for Certbot to do its magic.
1. It fetches the certificates from Let's Encrypt.
1. It creates a new copy of `nginx.conf` with all the settings you need to serve your website using SSL, and also redirects non-SSL traffic to the SSL version.
1. It leaves you with two files you can edit to suit your project:
   - `docker-compose.yml`: Be careful not to remove any of the 3 lines in the `volumes` section. Add as many other lines as you like, but keep the ones generated for you here intact.
   - `nginx.conf`: You probably don't need to touch the port 80 section at all (the `location /.well-known/acme-challenge/` section must remain so the certificates can renew). You can edit the port 443 section as you like but don't touch the `ssl_certificate` and `ssl_certificate_key` lines.

## Configuration

```
{
  "domain": "example.com",
  "email": "certbot@example.com",
  "legacy_compose": false,
  "nginx_image": "nginx:1.23.2-alpine",
  "volume_prefix": "./data"
}
```

- `domain` should be the FQDN of your website, e.g. _en.wikipedia.org_
- `email` is the email address you provide to Let's Encrypt
- `legacy_compose` when `true` when you use the v1 syntax of docker compose, i.e. `docker-compose` with the hyphen. Set to `false` if you use the modern `docker compose` without the hyphen.
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
server {
    listen 80;
    listen [::]:80;

    server_name _;
    server_tokens off;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://example.com$request_uri;
    }
}

server {
    listen 443 default_server ssl http2;
    listen [::]:443 ssl http2;

    server_name _;
    server_tokens off;

    ssl_certificate /etc/nginx/ssl/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/example.com/privkey.pem;

    location / {
        if ( $host !~* ^(example.com)$ ) {
            return 444;
        }

        # you will likely want to replace the following line with
        # your own configuration
        root /usr/share/nginx/html;
    }
}
```

## What do the cronjobs do?

The cronjobs work together to keep your certificates up-to-date. There are two parts to this:

1. Firstly, the `certbot renew` command tells Certbot to attempt to renew your certificates. If your current certificates are sufficiently close to expiry, it will update them with new ones.

   Unfortunately, this alone is not enough. We also need Nginx to `reload` its configuration so it can begin serving the new certificates instead of the old ones.

   Ideally, we'd use the Certbot `--post-hook` here, which runs a command or script after a successful renewal, but this isn't straightforward as we would need for our Certbot container to communicate directly with our Nginx container. Yes, it can be done, but I specifically wanted this project to be _as simple as possible_ and so I have chosen not to do it that way at this time. Instead...

2. The second command requests nginx `reload` itself at 5-past-midnight every night. This isn't elegant but it works: each time Nginx reloads, it will use the newest certificates it has available. There is no downtime when `reload` is called.

## Legal

Be aware, running this next command assumes you agree to the Let's Encrypt Subscriber Agreement. See: https://letsencrypt.org/documents/LE-SA-v1.5-February-24-2025.pdf. If you do not agree to these rules, please do NOT use this script.
