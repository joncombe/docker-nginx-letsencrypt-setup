# Save this in a file called certbot.json and edit as required
#
# {
#   "domain": "example.com",
#   "email": "certbot@example.com",
#   "nginx_image": "nginx:latest",
#   "volume_prefix": "./data"
# }

# Do not change anything below this line, unless you know what you are doing :)

import json
import os

DOCKER_COMPOSE_TEMPLATE = """version: '3'

services:
  webserver:
    image: [NGINX_IMAGE]
    ports:
      - 80:80
      - 443:443
    restart: always
    volumes:
      - [VOLUME_PREFIX]/certbot/conf/:/etc/nginx/ssl/:ro
      - [VOLUME_PREFIX]/certbot/www:/var/www/certbot/:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro

  certbot:
    image: certbot/certbot:latest
    volumes:
      - [VOLUME_PREFIX]/certbot/conf/:/etc/letsencrypt/:rw
      - [VOLUME_PREFIX]/certbot/www/:/var/www/certbot/:rw"""

LETSENCRYPT_TEMPLATE = "docker compose run --rm  certbot certonly --webroot --webroot-path /var/www/certbot/ [DRYRUN] -d [DOMAIN] --non-interactive --agree-tos -m [EMAIL]"

NGINX_PRE_TEMPLATE = """server {
    listen 80 default_server;
    listen [::]:80;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}"""

NGINX_POST_TEMPLATE = """server {
    listen 80;
    listen [::]:80;

    server_name _;
    server_tokens off;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://[DOMAIN]$request_uri;
    }
}

server {
    listen 443 default_server ssl http2;
    listen [::]:443 ssl http2;

    server_name _;
    server_tokens off;

    ssl_certificate /etc/nginx/ssl/live/[DOMAIN]/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/[DOMAIN]/privkey.pem;

    location / {
        if ( $host !~* ^([DOMAIN])$ ) {
            return 444;
        }

        # you will likely want to replace the following line with
        # your own configuration
        root /usr/share/nginx/html;
    }
}"""


class DockerNginxLetsEncryptSetup:
    def __init__(self):
        f = open("certbot.json")
        self.config = json.load(f)
        f.close()

        # TODO: validate the config, e.g.
        # - domain is a valid fqdn
        # - volume_prefix is a non-empty string
        # - email is a valid email string

    def cleanup(self):
        print(
            f"\n\nDone. Navigate to https://{self.config['domain']} in your browser..."
        )
        if input(
            f"\nRemove the setup files (if {self.config['domain']} has a valid certificate you don't need them anymore) (Y/n): "
        ) in ["", "y", "Y"]:
            os.remove("certbot.json")
            os.remove("certbot.py")
            print("Deleted the setup files.")
        print(
            "\nAdd the following line to your crontab to auto-renew this certificate:"
        )
        print("0 0,12 * * * docker compose run --rm certbot renew")
        print(
            "\nEdit the docker-compose.yml and nginx.conf files to suit your project, being careful that you:"
        )
        print(" 1) don't remove any of the 'volumes' lines in docker-compose.yml")
        print(" 2) don't remove any of the 'ssl_cert*' lines in nginx.conf")

    def get_certificate(self, dry_run=True):
        os.system(
            LETSENCRYPT_TEMPLATE.replace(
                "[DRYRUN]",
                "--dry-run" if dry_run else "",
            )
            .replace(
                "[DOMAIN]",
                self.config["domain"],
            )
            .replace(
                "[EMAIL]",
                self.config["email"],
            )
        )

    def setup(self):
        self.stop_docker()
        self.write_docker_compose_yml()
        self.write_pre_nginx_conf()
        self.start_docker()
        self.get_certificate(dry_run=False)
        self.stop_docker()
        self.write_post_nginx_conf()
        self.start_docker()
        self.cleanup()

    def start_docker(self):
        os.system("docker compose up -d")

    def stop_docker(self):
        if os.path.exists("docker-compose.yml"):
            os.system("docker compose down")

    def write_docker_compose_yml(self):
        self.write_file(
            "docker-compose.yml",
            DOCKER_COMPOSE_TEMPLATE.replace(
                "[NGINX_IMAGE]",
                self.config["nginx_image"],
            ).replace(
                "[VOLUME_PREFIX]",
                self.config["volume_prefix"],
            ),
        )

    def write_file(self, filename, contents):
        f = open(filename, "w")
        f.write(contents)
        f.close()

    def write_post_nginx_conf(self):
        self.write_file(
            "nginx.conf",
            NGINX_POST_TEMPLATE.replace(
                "[DOMAIN]",
                self.config["domain"],
            ),
        )

    def write_pre_nginx_conf(self):
        self.write_file("nginx.conf", NGINX_PRE_TEMPLATE)


if __name__ == "__main__":
    dnles = DockerNginxLetsEncryptSetup()
    dnles.setup()
