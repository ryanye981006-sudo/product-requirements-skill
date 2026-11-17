// Local browser regression: synthetic data only, no logged-in browser control.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'product-requirements-'));
  const output = path.join(folder, 'example.html');
  let browser;
  try {
    const conversion = spawnSync(process.env.PYTHON || 'python', [
      path.join(__dirname, 'convert.py'), path.join(root, 'assets/example.md'),
      '--output', output, '--title', '示例功能需求'
    ], {encoding: 'utf8'});
    assert.equal(conversion.status, 0, conversion.stderr || String(conversion.error));
    browser = await chromium.launch({headless: true, ...(process.env.BROWSER_CHANNEL ? {channel: process.env.BROWSER_CHANNEL} : {})});
    const context = await browser.newContext({permissions: ['clipboard-read', 'clipboard-write'], viewport: {width: 1366, height: 900}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(output).href);
    assert.equal(await page.getByRole('button', {name: /^复制本行：/}).count(), 4);
    // Capture the actual values passed to clipboardData.setData during a real click.
    await page.evaluate(() => {
      window.copyFormats = {};
      const original = DataTransfer.prototype.setData;
      DataTransfer.prototype.setData = function(type, value) {
        window.copyFormats[type] = value;
        return original.call(this, type, value);
      };
    });
    await page.getByRole('button', {name: '复制本行：查询', exact: true}).click();
    assert.equal(await page.locator('#copy-status').textContent(), '本行已复制');
    const formats = await page.evaluate(() => window.copyFormats);
    assert.deepEqual(Object.keys(formats).sort(), ['text/html', 'text/plain', 'text/ne-inode', 'text/lake'].sort());
    const grid = JSON.parse(formats['text/ne-inode']).children[0];
    const cells = grid.children[0].children;
    assert.equal(grid.attrs.colCount, 3);
    assert.equal(cells.length, 3);
    assert.deepEqual(cells.map(cell => cell.attrs.col), [0, 1, 2]);
    assert.equal(cells[0].children[0].children[0].data, '查询');
    assert.equal(cells[2].children[0].children.length, 0);
    assert.equal(cells[1].children.length, 3);
    assert(cells[1].children.every((item, index) => item.name === 'oli' && item.attrs.index === index && item.attrs.list === cells[1].children[0].attrs.list));
    assert.equal(cells[1].children[0].children.find(text => text.data === '关键字').attrs.bold, true);
    assert.equal(formats['text/plain'], '查询\t1. 输入关键字，点击【查询】。\n2. 展示匹配结果，保留原有顺序。\n3. 无匹配项时显示空提示。\t');
    assert(!formats['text/html'].includes('copy-row'));
    assert(!formats['text/html'].includes('复制本行'));
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    assert.equal(clipboard, formats['text/plain']);
    // Other table widths must not be forced into a three-column grid.
    await page.getByRole('button', {name: '复制本行：名称', exact: true}).click();
    assert.equal(await page.evaluate(() => JSON.parse(window.copyFormats['text/ne-inode']).children[0].attrs.colCount), 2);
    // Inline bold and separate paragraphs survive outside a list too.
    await page.getByRole('button', {name: '复制本行：特殊文本', exact: true}).click();
    const special = await page.evaluate(() => JSON.parse(window.copyFormats['text/ne-inode']).children[0].children[0].children[1].children);
    assert.equal(special.length, 2);
    assert(special[0].children.some(text => text.data === '重点内容' && text.attrs.bold));
    assert.equal(special[1].children[0].data, '第二行');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    // Some browsers reject custom types while allowing standard HTML/plain text.
    await page.evaluate(() => {
      window.previousSetData = DataTransfer.prototype.setData;
      DataTransfer.prototype.setData = function(type, value) {
        if (type === 'text/ne-inode') throw new Error('Custom clipboard type rejected');
        return window.previousSetData.call(this, type, value);
      };
    });
    await page.getByRole('button', {name: '复制本行：查询', exact: true}).click();
    assert((await page.locator('#copy-status').textContent()).startsWith('复制失败'));
    await page.evaluate(() => {DataTransfer.prototype.setData = window.previousSetData;});
    // A rejected copy must not be reported as successful or silently use plain text.
    await page.evaluate(() => {document.execCommand = () => false;});
    await page.getByRole('button', {name: '复制本行：查询', exact: true}).click();
    assert((await page.locator('#copy-status').textContent()).startsWith('复制失败'));
    assert.equal(await page.getByRole('button', {name: '复制本行：查询', exact: true}).isEnabled(), true);
    assert.deepEqual(errors, []);
    console.log('Passed: actual row copy, four MIME types, 2/3 columns, native lists, inline bold, line breaks, empty cell, clipboard text, failure state, layout.');
  } finally {
    if (browser) await browser.close();
    fs.rmSync(folder, {recursive: true, force: true});
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
