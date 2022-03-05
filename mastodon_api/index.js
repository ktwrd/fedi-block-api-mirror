const puppeteer = require("puppeteer");
const app = require("express")();
const PORT = 8069;

async function main(domain, _callback) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    let data;
    try {
        await page.goto("https://"+domain+"/about/more", {waitUntil: "networkidle2"});
        data = await page.evaluate(() => {
            let reject = []; // Suspended servers
            let media_removal = []; // Filtered media
            let federated_timeline_removal = []; // Silenced servers, Limited servers
            Array.from(document.querySelectorAll("table")).map(table => {
                if (["Suspended servers","Filtered media","Limited servers", "Silenced servers"].includes(table.previousElementSibling.previousElementSibling.innerText)) {
                    Array.from(table.rows).map((row, j) => {
                        if (j == 0)
                            return;

                        let row_obj = {
                            domain: row.childNodes[1].innerText,
                            hash: row.querySelector("[title]").title.replace("SHA-256: ", ""),
                            reason: row.childNodes[3].innerText,
                        }

                        switch(table.previousElementSibling.previousElementSibling.innerText) {
                            case "Suspended servers":
                                reject.push(row_obj);
                                break;
                            case "Filtered media":
                                media_removal.push(row_obj);
                                break;
                            case "Limited servers":
                            case "Silenced servers":
                                federated_timeline_removal.push(row_obj);
                                break;
                        }
                    });
                }
            });
            return {
                reject,
                media_removal,
                federated_timeline_removal,
            }
        })
    } catch(err) {
        console.log(err.message);
    }
    _callback(data);
    await browser.close();
}

app.listen(PORT, "127.0.0.1", () => console.log("API started on http://127.0.0.1:"+PORT));
app.get("/", (req, res) => {
    res.status(400).send({"message":"insert a domain"});
});
app.get("/:domain", (req, res) => {
    const {domain} = req.params;
    main(domain, data => res.status(200).send({
        "reject": data.reject,
        "media_removal": data.media_removal,
        "federated_timeline_removal": data.federated_timeline_removal,
    }));
});
