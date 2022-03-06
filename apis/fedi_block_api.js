const app = require("express")();
const sqlite3 = require('sqlite3').verbose();
const PORT = 8070;

const db = new sqlite3.Database("../blocks.db", sqlite3.OPEN_READONLY, err => {
    if (err)
        return console.error(err.message);
});

app.listen(PORT, "127.0.0.1", () => console.log("API started on http://127.0.0.1:"+PORT));
app.get("/", (req, res) => {
    res.status(400).send({"message":"insert a domain"});
});

function get_blocker(blocker, _callback, _err_callback) {
    db.all("select blocked, reason, block_level from blocks where blocker = ?", blocker, (err, result) => {
        if (err) {
            _err_callback(err)
            return console.error(err.message);
        }
        _callback(result);
    });
}

function get_blocked(blocked, _callback, _err_callback) {
    db.all("select blocker, reason, block_level from blocks where blocked = ?", blocked, (err, result) => {
        if (err) {
            _err_callback(err);
            return console.error(err.message);
        }
        _callback(result);
    });
}

app.get("/blocker/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocker(
        domain,
        result => res.status(200).send({result}),
        err => res.status(500).send({"message": err}),
    );
});

app.get("/blocked/:domain", (req, res) => {
    const {domain} = req.params;
    get_blocked(
        domain,
        result => res.status(200).send({result}),
        err => res.status(500).send({"message": err}),
    );
});
