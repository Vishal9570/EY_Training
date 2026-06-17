const express = require("express");

const app = express();
const PORT = 8000;

app.get("/", (req, res) => {
  res.send("Hello, Docker Node.js App is running!");
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});