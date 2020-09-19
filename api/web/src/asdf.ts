import express from "express";
const app = express();
app.use(express.static("public"));
app.listen(9000, (): void => { console.log("started"); });
