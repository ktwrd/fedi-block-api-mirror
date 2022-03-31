# Fedi block API

Used to see which instances block yours.

## software used:

- python 3.10.2
- [node v17.6.0](https://github.com/nodesource/distributions/blob/master/README.md#installation-instructions)
- [yarn 1.22.17](https://classic.yarnpkg.com/en/docs/install#debian-stable)

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

### Install node packages

```bash
cd apis
sudo -Hu fba yarn install
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
