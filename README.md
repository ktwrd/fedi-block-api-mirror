# Fedi block API

Used to see which instances block yours.

## software used:

- python 3.10.2
- [node v17.6.0](https://github.com/nodesource/distributions/blob/master/README.md#installation-instructions)
- [yarn 1.22.17](https://classic.yarnpkg.com/en/docs/install#debian-stable)

## Installation

### Copy the preloaded database to the live database

```bash
cp blocks_preloaded.db blocks.db
```

### Install the services

Make sure to edit the `User` and `WorkingDirectory` in each service file accordingly.

```bash
sudo cp services/* /etc/systemd/system
```

### Install node packages

```bash
cd apis
yarn install
```

### start the services

```bash
systemctl start mastodon_api
systemctl start fetch_blocks
systemctl start fedi_block_api
```

## Try it out

https://api.chizu.love/blocked/

## License

[AGPLv3+NIGGER](https://plusnigger.autism.exposed/)
