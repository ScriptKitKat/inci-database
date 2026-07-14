import { randomBytes, scryptSync } from "node:crypto";

const password = process.argv[2];
if (!password) throw new Error("usage: node scripts/hash-password.mjs <password>");
const salt = randomBytes(16);
const hash = scryptSync(password, salt, 64);
process.stdout.write(`${salt.toString("hex")}:${hash.toString("hex")}\n`);
