const app = require("express")();
const sqlite3 = require('sqlite3').verbose();
const PORT = 8070;

const db = new sqlite3.Database("../blocks.db", sqlite3.OPEN_READONLY, err => {
    if (err)
        return console.error(err.message);
});

app.listen(PORT, "127.0.0.1", () => console.log("API started on http://127.0.0.1:"+PORT));
app.get("/", (req, res) => {
    res.status(400).json({"message":"use /blocker, /blocked or /info endpoint"});
});
app.get("/blocker", (req, res) => {
    res.status(400).json({"message":"insert a domain"});
});
app.get("/blocked", (req, res) => {
    res.status(400).json({"message":"insert a domain"});
});

app.get("/info", (req, res) => {
    db.all("select (select count(domain) from instances) as known, (select count(domain) from instances where software in ('pleroma', 'mastodon')) as indexed, (select count(blocker) from blocks) as blocks", (err, result) => {
        if (err) {
            res.status(500).json({"message": err});
            console.log(err.message);
            return;
        }
        res.status(200).json({
            "known_instances": result[0]["known"],
            "indexed_instances": result[0]["indexed"],
            "blocks_recorded": result[0]["blocks"],
        });
    });
});

function get_blocker(blocker, _callback, _err_callback) {
    db.all("select blocked, block_level from blocks where blocker = ?", blocker, (err, result) => {
        if (err) {
            _err_callback(err);
            console.log(err.message);
            return;
        }
        reject = [];
        media_removal = [];
        federated_timeline_removal = [];
        media_nsfw = [];
        quarantined_instances = [];
        report_removal = [];
        followers_only = [];
        accept = [];
        avatar_removal = [];
        banner_removal = [];
        reject_deletes = [];

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
                case "report_removal":
                    report_removal.push(block.blocked);
                    break;
                case "followers_only":
                    followers_only.push(block.blocked);
                    break;
                case "accept":
                    accept.push(block.blocked);
                    break;
                case "avatar_removal":
                    avatar_removal.push(block.blocked);
                    break;
                case "banner_removal":
                    banner_removal.push(block.blocked);
                    break;
                case "reject_deletes":
                    reject_deletes.push(block.blocked);
                    break;
            }
        });
        _callback({
            reject,
            media_removal,
            federated_timeline_removal,
            media_nsfw,
            quarantined_instances,
            report_removal,
            followers_only,
            accept,
            avatar_removal,
            banner_removal,
            reject_deletes,
        });
    });
}

function get_blocked(blocked, _callback, _err_callback) {
    db.all("select blocker, block_level from blocks where blocked = ?", blocked, (err, result) => {
        if (err) {
            _err_callback(err);
            console.log(err.message);
            return;
        }
        reject = [];
        media_removal = [];
        federated_timeline_removal = [];
        media_nsfw = [];
        quarantined_instances = [];
        report_removal = [];
        followers_only = [];
        accept = [];
        avatar_removal = [];
        banner_removal = [];
        reject_deletes = [];

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
                case "report_removal":
                    report_removal.push(block.blocker);
                    break;
                case "followers_only":
                    followers_only.push(block.blocker);
                    break;
                case "accept":
                    accept.push(block.blocker);
                    break;
                case "avatar_removal":
                    avatar_removal.push(block.blocker);
                    break;
                case "banner_removal":
                    banner_removal.push(block.blocker);
                    break;
                case "reject_deletes":
                    reject_deletes.push(block.blocker);
                    break;
            }
        });
        _callback({
            reject,
            media_removal,
            federated_timeline_removal,
            media_nsfw,
            quarantined_instances,
            report_removal,
            followers_only,
            accept,
            avatar_removal,
            banner_removal,
            reject_deletes,
        });
    });
}

app.get("/blocker/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocker(
        domain,
        result => res.status(200).json(result),
        err => res.status(500).json({"message": err}),
    );
});

app.get("/blocked/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocked(
        domain,
        result => res.status(200).json(result),
        err => res.status(500).json({"message": err}),
    );
});
