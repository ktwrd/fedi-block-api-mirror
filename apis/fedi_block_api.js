const app = require("express")();
const sqlite3 = require('sqlite3').verbose();
const PORT = 8070;

const db = new sqlite3.Database("../blocks.db", sqlite3.OPEN_READONLY, err => {
    if (err)
        return console.error(err.message);
});

app.listen(PORT, "127.0.0.1", () => console.log("API started on http://127.0.0.1:"+PORT));
app.get("/", (req, res) => {
    res.status(400).send({"message":"use /blocker or /blocked endpoint"});
});
app.get("/blocker", (req, res) => {
    res.status(400).send({"message":"insert a domain"});
});
app.get("/blocked", (req, res) => {
    res.status(400).send({"message":"insert a domain"});
});

function get_blocker(blocker, _callback, _err_callback) {
    db.all("select blocked, block_level from blocks where blocker = ?", blocker, (err, result) => {
        if (err) {
            _err_callback(err)
            return console.error(err.message);
        }
        reject = [];
        media_removal = [];
        federated_timeline_removal = [];
        media_nsfw = [];
        quarantined_instances = [];
        other = [];
        result.map(block => {
            switch(block.block_level) {
                case "reject":
                    reject.push(block.blocked);
                    break;
                case "media_removal":
                    media_removal.push(block.blocked);
                    break;
                case "federated_timeline_removal":
                    federated_timeline_removal.push(block.blocked);
                    break;
                case "media_nsfw":
                    media_nsfw.push(block.blocked);
                    break;
                case "quarantined_instances":
                    quarantined_instances.push(block.blocked);
                    break;
                default:
                    other.push({
                        "blocked": block.blocked,
                        "block_level": block.block_level,
                    });
            }
        });
        _callback({
            reject,
            media_removal,
            federated_timeline_removal,
            media_nsfw,
            quarantined_instances,
            other,
        });
    });
}

function get_blocked(blocked, _callback, _err_callback) {
    db.all("select blocker, block_level from blocks where blocked = ?", blocked, (err, result) => {
        if (err) {
            _err_callback(err);
            return console.error(err.message);
        }
        reject = [];
        media_removal = [];
        federated_timeline_removal = [];
        media_nsfw = [];
        quarantined_instances = [];
        other = [];
        result.map(block => {
            switch(block.block_level) {
                case "reject":
                    reject.push(block.blocker);
                    break;
                case "media_removal":
                    media_removal.push(block.blocker);
                    break;
                case "federated_timeline_removal":
                    federated_timeline_removal.push(block.blocker);
                    break;
                case "media_nsfw":
                    media_nsfw.push(block.blocker);
                    break;
                case "quarantined_instances":
                    quarantined_instances.push(block.blocker);
                    break;
                default:
                    other.push({
                        "blocker": block.blocker,
                        "block_level": block.block_level,
                    });
            }
        });
        _callback({
            reject,
            media_removal,
            federated_timeline_removal,
            media_nsfw,
            quarantined_instances,
            other,
        });
    });
}

app.get("/blocker/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocker(
        domain,
        result => res.status(200).send(result),
        err => res.status(500).send({"message": err}),
    );
});

app.get("/blocked/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocked(
        domain,
        result => res.status(200).send(result),
        err => res.status(500).send({"message": err}),
    );
});
