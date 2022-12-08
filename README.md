This script sets up a Let's Encrypt certificate on an Nginx webserver for use in a Docker environment. It only takes a minute.

There is an _excellent_ blog post on this topic, [HTTPS using Nginx and Let's encrypt in Docker](https://mindsers.blog/post/https-using-nginx-certbot-docker/), which has helped me many, many times (_thank you, Nathanaël_). This script goes through very similar steps to what is described in that blog post, but in a completely automated way.

> This script has been tested on Ubuntu servers. I think it will work on any Linux environment with Docker installed but I'd appreciate your feedback on that.

To get started, be sure that your DNS already is configured and has propagated. `ssh` into your target server and copy the `certbot.py` and `certbot.json` files from this repo to your directory.

Here, let me help you:

```
curl -o certbot.py https://raw.githubusercontent.com/joncombe/docker-nginx-letsencrypt-setup/main/certbot.py
curl -o certbot.json https://raw.githubusercontent.com/joncombe/docker-nginx-letsencrypt-setup/main/certbot.json
```

Next, edit the `certbot.json` file:

- `domain` should be the FQDN of your website, e.g. "en.wikipedia.org"
- `email` is the email address you provide to Let's Encrypt
- `nginx_image` is the name of the nginx image to use. Leaving it the default value will be fine for most of you
- `volume_prefix` is the local path to the location your persisted docker data files are stored. If you are not sure what to do here, leave it as it is. _[TODO: improve how to explain this, my terminology has failed me]_.

> Be aware, running this next command assumes you agree to the Let's Encrypt Terms of Service. See: https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf. If you do not agree to these rules, please do NOT use this script.

Once this is done, run the script:

```
python3 certbot.py
```

All done. There, wasn't that easy?

At the end of it all, you will be left with your certificates and new `docker-compose.yml` and `nginx.conf` files. Edit these to suit your project but be careful not to remove any of the `volumes` lines in the `docker-compose.yml`, and don't remove the `ssl_cert*` lines in `nginx.conf`.
