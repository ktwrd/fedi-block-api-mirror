# Fedi block API

Used to see which instances block yours.

## software used:
- python 3.10.2
- node v17.6.0
- yarn 1.22.17

## how to use:

Copy the preloaded database to the live database

`cp blocks_preloaded.db blocks.db`

Start the mastodon API

Make sure to edit the `User` and `WorkingDirectory` of the service file accordingly.

```
sudo cp services/mastodon_api.service /etc/systemd/system
cd mastodon_api
yarn install
systemctl start mastodon_api
```

Fill the database with blocks.

`python fetch_blocks.py`

## License

[AGPLv3+NIGGER](https://plusnigger.autism.exposed/)