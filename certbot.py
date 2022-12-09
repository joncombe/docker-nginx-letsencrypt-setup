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


def cleanup():
    print(f"\n\nDone. Navigate to https://{config['domain']} in your browser...")
    if input(
        f"\nRemove the setup files (if {config['domain']} has a valid certificate you don't need them anymore) (Y/n): "
    ) in ["", "y", "Y"]:
        os.remove("certbot.json")
        os.remove("certbot.py")
        print("Deleted the setup files.")
    print("\nAdd the following line to your crontab to auto-renew this certificate:")
    print("0 0,12 * * * docker compose run --rm certbot renew")
    print(
        "\nNow go ahead and edit the docker-compose.yml and nginx.conf files, being careful that you:"
    )
    print(" 1) don't remove any of the 'volumes' lines in docker-compose.yml")
    print(" 2) don't remove any of the 'ssl_cert*' lines in nginx.conf")


def get_certificate(config, dry_run=True):
    os.system(
        f"docker compose run --rm  certbot certonly --webroot --webroot-path /var/www/certbot/ {'--dry-run' if dry_run else ''} -d {config['domain']} --non-interactive --agree-tos -m {config['email']}"
    )


def load_config():
    f = open("certbot.json")
    config = json.load(f)
    f.close()

    # TODO: validate the config, e.g.
    # - domain is a valid fqdn
    # - volume_prefix is a non-empty string
    # - email is a valid email string

    return config


def start_docker():
    os.system("docker compose up -d")


def stop_docker():
    if os.path.exists("docker-compose.yml"):
        os.system("docker compose down")


def write_docker_compose_yml(config):
    write_file(
        "docker-compose.yml",
        f"""version: '3'

services:
  webserver:
    image: {config['nginx_image']}
    ports:
      - 80:80
      - 443:443
    restart: always
    volumes:
      - {config['volume_prefix']}/certbot/conf/:/etc/nginx/ssl/:ro
      - {config['volume_prefix']}/certbot/www:/var/www/certbot/:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro

  certbot:
    image: certbot/certbot:latest
    volumes:
      - {config['volume_prefix']}/certbot/conf/:/etc/letsencrypt/:rw
      - {config['volume_prefix']}/certbot/www/:/var/www/certbot/:rw
  """,
    )


def write_file(name, contents):
    f = open(name, "w")
    f.write(contents)
    f.close()


def write_post_nginx_conf(config):
    write_file(
        "nginx.conf",
        f"""server {{
    listen 80;
    listen [::]:80;

    server_name _;
    server_tokens off;

    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}

    location / {{
        return 301 https://{config['domain']}$request_uri;
    }}
}}

server {{
    listen 443 default_server ssl http2;
    listen [::]:443 ssl http2;

    server_name _;
    server_tokens off;

    ssl_certificate /etc/nginx/ssl/live/{config['domain']}/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/{config['domain']}/privkey.pem;

    location / {{
        if ( $host !~* ^({config['domain']})$ ) {{
            return 444;
        }}

        # you will likely want to replace the following line with
        # your own configuration
        root /usr/share/nginx/html;
    }}
}}""",
    )


def write_pre_nginx_conf(config):
    write_file(
        "nginx.conf",
        """server {
    listen 80 default_server;
    listen [::]:80;

    location /.well-known/acme-challenge/ {
      root /var/www/certbot;
    }

    location / {
      return 301 https://$host$request_uri;
    }
}""",
    )


if __name__ == "__main__":
    config = load_config()
    stop_docker()
    write_docker_compose_yml(config)
    write_pre_nginx_conf(config)
    start_docker()
    get_certificate(config, dry_run=False)
    stop_docker()
    write_post_nginx_conf(config)
    start_docker()
    cleanup()
