// Copies the static site plus the repo's shared data (skills taxonomy and
// task board) into dist/, so the live site always renders the repo's files.
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const site = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(site, "..");
const dist = join(site, "dist");

rmSync(dist, { recursive: true, force: true });
cpSync(join(site, "public"), dist, { recursive: true });
mkdirSync(join(dist, "data"), { recursive: true });
cpSync(join(repo, "aipath/data/skills.json"), join(dist, "data/skills.json"));
cpSync(join(repo, "tasks.json"), join(dist, "data/tasks.json"));
console.log("Built site/dist");
