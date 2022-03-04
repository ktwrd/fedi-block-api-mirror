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

```
cd mastodon_api
yarn install
node .
```

Fill the database with blocks.

`python fetch_blocks.py`

## License

[AGPLv3+NIGGER](https://plusnigger.autism.exposed/)