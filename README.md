# Fedi block API

Used to see which instances block yours.

## software used:

- python 3.10.2

## Installation

```bash
sudo useradd -m fba
sudo mkdir -p /opt/fedi-block-api
sudo chown -R fba:fba /opt/fedi-block-api
sudo -Hu fba git clone https://gitlab.com/EnjuAihara/fedi-block-api.git /opt/fedi-block-api
cd /opt/fedi-block-api
sudo -Hu fba cp blocks_preloaded.db blocks.db
```

### Install the services

```bash
sudo cp services/* /etc/systemd/system
```

### start the services

```bash
systemctl enable --now fetch_blocks
systemctl enable --now fedi_block_api
```

## Try it out

https://chizu.love/fedi-block-api/api

## License

[AGPLv3+NIGGER](https://plusnigger.autism.exposed/)
