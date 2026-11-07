#!/usr/bin/env node
/**
 * Mengaudit kelengkapan TSDoc berbahasa Indonesia pada kode frontend.
 *
 * Aturan cakupan mengikuti tabel "Kapan Wajib TSDoc" di SKILL.md:
 * ekspor di hooks/, lib/, types/, context/, dan components/ wajib ber-TSDoc;
 * folder app/ tidak diwajibkan. Memakai paket `typescript` dari frontend/node_modules.
 *
 * Pemakaian:
 *   node .agents/skills/tsdoc-id/scripts/audit_tsdoc.cjs <path...> [--summary]
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ts = loadTypeScript();

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx"]);
const IGNORED_DIRS = new Set(["node_modules", ".next", "e2e", "test-results", "playwright-report", "public"]);
const IGNORED_FILE_PATTERN = /(\.d\.ts|\.test\.tsx?|\.spec\.tsx?)$/;
const ENGLISH_MARKERS = new Set([
  "the", "returns", "return", "this", "that", "is", "are", "for", "of", "and", "with",
  "fetch", "fetches", "get", "gets", "used", "when", "from", "component", "which", "should",
]);
const ENGLISH_MARKER_THRESHOLD = 2;
const BANNER_COMMENT_PATTERN = /^[-=*#]{3,}/;
const COMMENTED_CODE_PATTERN =
  /^(const|let|var|import|export|return|await|if\s*\(|for\s*\(|console\.|set[A-Z]\w*\(|<\/?[A-Za-z][\w.]*[\s>/])|[;{}]\s*$/;

function loadTypeScript() {
  const candidates = [path.resolve("frontend/node_modules/typescript"), "typescript"];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch {
      continue;
    }
  }
  console.error("Paket `typescript` tidak ditemukan. Jalankan `npm install` di frontend/.");
  process.exit(2);
}

function classifyScope(filePath) {
  const normalized = filePath.split(path.sep).join("/");
  if (/\/app\//.test(normalized)) return null;
  if (/\/hooks\//.test(normalized)) return "hook";
  if (/\/context\//.test(normalized)) return "context";
  if (/\/lib\/types\.ts$/.test(normalized) || /\/types\//.test(normalized)) return "types";
  if (/\/lib\//.test(normalized)) return "lib";
  if (/\/components\//.test(normalized)) return "component";
  return null;
}

function collectFiles(target, files = []) {
  if (!fs.existsSync(target)) {
    console.error(`Path tidak ditemukan: ${target}`);
    return files;
  }
  const stat = fs.statSync(target);
  if (stat.isFile()) {
    if (SOURCE_EXTENSIONS.has(path.extname(target)) && !IGNORED_FILE_PATTERN.test(target)) files.push(target);
    return files;
  }
  for (const entry of fs.readdirSync(target)) {
    if (IGNORED_DIRS.has(entry)) continue;
    collectFiles(path.join(target, entry), files);
  }
  return files;
}

function isExported(node) {
  const modifiers = ts.canHaveModifiers(node) ? ts.getModifiers(node) : undefined;
  return Boolean(modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword));
}

function getJsDocs(node) {
  return (node.jsDoc ?? []).filter((doc) => doc.kind === ts.SyntaxKind.JSDoc);
}

function docSummary(doc) {
  const comment = doc.comment;
  if (!comment) return "";
  if (typeof comment === "string") return comment;
  return comment.map((part) => part.text ?? "").join("");
}

function isFunctionLike(node) {
  return node && (ts.isArrowFunction(node) || ts.isFunctionExpression(node) || ts.isFunctionDeclaration(node));
}

function unwrapInitializer(initializer) {
  let current = initializer;
  while (current && ts.isCallExpression(current) && current.arguments.length > 0) {
    const first = current.arguments[0];
    if (isFunctionLike(first)) return first;
    current = first;
  }
  return current;
}

function hasValueReturn(fn) {
  if (!fn.body) return false;
  if (!ts.isBlock(fn.body)) return true;
  let found = false;
  const visit = (node) => {
    if (found || (node !== fn.body && isFunctionLike(node))) return;
    if (ts.isReturnStatement(node) && node.expression) {
      found = true;
      return;
    }
    ts.forEachChild(node, visit);
  };
  visit(fn.body);
  return found;
}

function returnsJsx(fn) {
  let found = false;
  const visit = (node) => {
    if (found || (node !== fn && isFunctionLike(node))) return;
    if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) || ts.isJsxFragment(node)) {
      found = true;
      return;
    }
    ts.forEachChild(node, visit);
  };
  if (fn.body) visit(fn.body);
  return found;
}

function collectExportedDeclarations(sourceFile) {
  const declarations = [];
  for (const statement of sourceFile.statements) {
    if (!isExported(statement)) continue;
    if (ts.isFunctionDeclaration(statement)) {
      declarations.push({ name: statement.name?.text ?? "default", kind: "function", docHost: statement, fn: statement });
    } else if (ts.isClassDeclaration(statement)) {
      declarations.push({ name: statement.name?.text ?? "default", kind: "class", docHost: statement });
    } else if (ts.isInterfaceDeclaration(statement) || ts.isTypeAliasDeclaration(statement) || ts.isEnumDeclaration(statement)) {
      declarations.push({ name: statement.name.text, kind: "type", docHost: statement });
    } else if (ts.isVariableStatement(statement)) {
      for (const decl of statement.declarationList.declarations) {
        const fn = unwrapInitializer(decl.initializer);
        if (!isFunctionLike(fn) || !ts.isIdentifier(decl.name)) continue;
        declarations.push({ name: decl.name.text, kind: "function", docHost: statement, fn });
      }
    }
  }
  return declarations;
}

function isRequired(scope, declaration) {
  if (scope === "component") {
    // Pada direktori components, hanya komponen React utama (fungsi PascalCase/class) yang wajib ber-TSDoc.
    // Interface Props dan helper utilitas lokal (camelCase) tidak diwajibkan TSDoc boilerplate terpisah.
    if (declaration.kind === "function") {
      return /^[A-Z]/.test(declaration.name);
    }
    if (declaration.kind === "class") return true;
    return false;
  }
  return true;
}

function looksEnglish(text) {
  const words = text.toLowerCase().match(/[a-z]+/g) ?? [];
  const markerCount = words.filter((word) => ENGLISH_MARKERS.has(word)).length;
  return markerCount >= ENGLISH_MARKER_THRESHOLD;
}

function auditParams(declaration, docs, report) {
  const fn = declaration.fn;
  const isComponent = returnsJsx(fn);
  const paramTags = docs.flatMap((doc) => (doc.tags ?? []).filter(ts.isJSDocParameterTag));
  const documented = new Set(paramTags.map((tag) => tag.name.getText()));
  const identifierParams = fn.parameters.filter((p) => ts.isIdentifier(p.name)).map((p) => p.name.text);

  if (!isComponent) {
    for (const param of identifierParams) {
      if (!documented.has(param)) report("PARAM", `\`${declaration.name}\`: @param \`${param}\` belum dijelaskan`);
    }
  }
  const allParams = new Set(fn.parameters.map((p) => p.name.getText()));
  for (const name of documented) {
    if (!name.includes(".") && !allParams.has(name) && identifierParams.length > 0) {
      report("PARAM", `\`${declaration.name}\`: @param \`${name}\` tidak ada di signature`);
    }
  }

  const hasReturnsTag = docs.some((doc) => (doc.tags ?? []).some((tag) => ts.isJSDocReturnTag(tag)));
  if (!isComponent && hasValueReturn(fn) && !hasReturnsTag) {
    report("RETURNS", `\`${declaration.name}\`: @returns belum ada`);
  }
}

function auditCommentedCode(sourceFile, report) {
  const text = sourceFile.getFullText();
  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, sourceFile.languageVariant, text);
  for (let token = scanner.scan(); token !== ts.SyntaxKind.EndOfFileToken; token = scanner.scan()) {
    if (token !== ts.SyntaxKind.SingleLineCommentTrivia) continue;
    const body = scanner.getTokenText().replace(/^\/\/\s?/, "").trim();
    if (/^(eslint|@ts-|prettier|TODO|FIXME)/.test(body)) continue;
    const { line } = sourceFile.getLineAndCharacterOfPosition(scanner.getTokenPos());
    if (BANNER_COMMENT_PATTERN.test(body)) {
      report("BANNER-STRIP", `dilarang komentar banner/strip dekoratif: "${body.slice(0, 50)}"`, line + 1);
      continue;
    }
    if (COMMENTED_CODE_PATTERN.test(body)) {
      report("KODE-KOMENTAR", `kemungkinan kode yang dikomentari: "${body.slice(0, 60)}"`, line + 1);
    }
  }
}

function auditFile(filePath) {
  const findings = [];
  const scope = classifyScope(path.resolve(filePath));
  const source = fs.readFileSync(filePath, "utf8");
  const kind = filePath.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sourceFile = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true, kind);

  const makeReporter = (node) => (category, message, explicitLine) => {
    const line = explicitLine ?? sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
    findings.push({ line, category, message });
  };

  if (scope) {
    for (const declaration of collectExportedDeclarations(sourceFile)) {
      if (!isRequired(scope, declaration)) continue;
      const report = makeReporter(declaration.docHost);
      const docs = getJsDocs(declaration.docHost);
      if (docs.length === 0) {
        report("TANPA-TSDOC", `\`${declaration.name}\` (${declaration.kind}) belum memiliki TSDoc`);
        continue;
      }
      const summary = docs.map(docSummary).join(" ");
      if (!summary.trim()) report("RINGKASAN", `\`${declaration.name}\`: ringkasan TSDoc kosong`);
      if (looksEnglish(summary)) report("BAHASA", `\`${declaration.name}\`: TSDoc tampak berbahasa Inggris`);
      if (declaration.fn && (scope === "hook" || scope === "lib" || scope === "context")) {
        auditParams(declaration, docs, report);
      }
    }
  }
  auditCommentedCode(sourceFile, makeReporter(sourceFile));
  return findings.sort((a, b) => a.line - b.line);
}

function main() {
  const args = process.argv.slice(2);
  const summaryOnly = args.includes("--summary");
  const targets = args.filter((arg) => !arg.startsWith("--"));
  if (targets.length === 0) {
    console.error("Pemakaian: node audit_tsdoc.cjs <path...> [--summary]");
    process.exit(2);
  }

  const files = targets.flatMap((target) => collectFiles(target));
  const totals = {};
  let totalFindings = 0;

  for (const file of files) {
    const findings = auditFile(file);
    if (findings.length === 0) continue;
    totalFindings += findings.length;
    for (const finding of findings) totals[finding.category] = (totals[finding.category] ?? 0) + 1;
    const relative = path.relative(process.cwd(), file);
    if (summaryOnly) {
      console.log(`${String(findings.length).padStart(4)}  ${relative}`);
      continue;
    }
    for (const finding of findings) {
      console.log(`${relative}:${finding.line} [${finding.category}] ${finding.message}`);
    }
  }

  console.log(`\nBerkas diperiksa: ${files.length} | Total temuan: ${totalFindings}`);
  for (const [category, count] of Object.entries(totals)) console.log(`  ${category}: ${count}`);
  process.exit(totalFindings > 0 ? 1 : 0);
}

main();

