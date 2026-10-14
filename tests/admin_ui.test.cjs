const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function panel(apiHandler) {
    const elements = new Map();
    const get = id => {
        if (!elements.has(id)) elements.set(id, {id, value: '', innerHTML: '', textContent: '', disabled: false, dataset: {}, attrs: {}, events: {},
            setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(k, f) { this.events[k] = f; }, focus() {},
        });
        return elements.get(id);
    };
    const tabs = ['scans', 'monitors', 'alerts', 'targets', 'recon'].map(r => { const e = get('admin-tab-' + r); e.dataset.operation = r; return e; });
    let loader;
    const context = vm.createContext({
        document: {body: {dataset: {uid: '1', role: 'admin'}}, querySelectorAll: () => tabs, addEventListener() {}},
        $: get, esc: v => String(v).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'),
        api: async url => {
            if (url === '/api/plans') return {plans: []};
            if (url === '/api/admin/overview') return {by_plan: [], users_total: 1, admins: 1, moderators: 0, disabled: 0, mrr: 0, revenue_total: 0, payments_total: 0, scans_today: 0, scans_total: 0, ai_today: 0, monitors_active: 0, alerts_7d: 0, failed_logins_24h: 0, sessions_active: 1, active_scans: 0, version: '9', codename: 'Cortex', uptime: 1, settings: {}, series: []};
            if (url.startsWith('/api/admin/users') || url.startsWith('/api/admin/payments') || url === '/api/admin/team') return [];
            if (url.startsWith('/api/admin/audit')) return {actions: {}, entries: []};
            if (url === '/api/admin/settings') return {plugins: [], session_days: 7, payment_mode: 'off'};
            return apiHandler(url);
        },
        toast() {}, hms: () => '1', VIEWS: {}, location: {hash: ''}, onPage: (_, f) => loader = f,
        isTyping: () => false, go() {}, route() {}, setTimeout, clearTimeout, console,
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/js/admin.js'), 'utf8'), context);
    return {get, tabs, load: () => loader()};
}
const scan = id => ({id, name: 'Operatör', email: 'member@example.com', target: '<img src=x>', ip_address: '192.0.2.1', risk_score: 70, risk_level: 'Yüksek', open_count: 2, scan_time: '2026-10-13', has_report: 1});
const tick = () => new Promise(resolve => setImmediate(resolve));

test('scan pagination preserves account ownership and escapes target markup', async () => {
    const p = panel(async url => {
        const offset = Number(new URL(url, 'http://local').searchParams.get('offset'));
        return offset ? {total: 26, items: [scan(1)]} : {total: 26, items: Array.from({length: 25}, (_, i) => scan(26-i))};
    });
    await p.load();
    assert.equal(p.get('adminOperationCount').textContent, '1–25 / 26 kayıt');
    assert.match(p.get('adminOperationRows').innerHTML, /member@example.com/);
    assert.match(p.get('adminOperationRows').innerHTML, /&lt;img src=x&gt;/);
    assert.doesNotMatch(p.get('adminOperationRows').innerHTML, /<img/);
    assert.ok(p.get('adminOperationRows').innerHTML.includes('/admin/reports/26'));
    assert.equal(p.get('adminOperationNext').disabled, false);
    p.get('adminOperationNext').events.click();
    await tick();
    assert.equal(p.get('adminOperationCount').textContent, '26–26 / 26 kayıt');
    assert.equal(p.get('adminOperationNext').disabled, true);
    assert.equal(p.get('adminOperationPrev').disabled, false);
});

test('switching tabs ignores a late scan response and renders monitor state', async () => {
    let resolveScan;
    const p = panel(url => url.startsWith('/api/admin/scans') ? new Promise(resolve => resolveScan = resolve) : Promise.resolve({total: 1, items: [{id: 8, name: 'Üye', email: 'owner@example.com', target: 'example.com', interval: 'daily', enabled: 0, next_run: '2026-10-14', last_status: 'Bekliyor', has_webhook: 1}]}));
    const loading = p.load();
    await tick();
    p.tabs[1].events.click();
    await tick();
    resolveScan({total: 1, items: [scan(9)]});
    await loading;
    assert.match(p.get('adminOperationRows').innerHTML, /Duraklatıldı/);
    assert.match(p.get('adminOperationRows').innerHTML, /Webhook: Bağlı/);
    assert.doesNotMatch(p.get('adminOperationRows').innerHTML, /192.0.2.1/);
    assert.equal(p.tabs[1].attrs['aria-selected'], 'true');
    assert.equal(p.get('adminOperationContent').attrs['aria-busy'], 'false');
});

test('operation failures produce a retry message instead of leaving stale rows', async () => {
    const p = panel(async () => { throw new Error('Bağlantı kesildi'); });
    await p.load();
    assert.match(p.get('adminOperationRows').innerHTML, /Bağlantı kesildi/);
    assert.equal(p.get('adminOperationNext').disabled, true);
    assert.equal(p.get('adminOperationContent').attrs['aria-busy'], 'false');
});

test('search resets pagination and URL encodes the query', async () => {
    const urls = [];
    const p = panel(async url => { urls.push(url); return {total: 30, items: [scan(1)]}; });
    await p.load();
    p.get('adminOperationNext').events.click();
    await tick();
    p.get('adminOperationSearch').value = 'member+tag@example.com';
    p.get('adminOperationSearch').events.input();
    await new Promise(resolve => setTimeout(resolve, 280));
    assert.equal(new URL(urls.at(-1), 'http://local').searchParams.get('q'), 'member+tag@example.com');
    assert.equal(new URL(urls.at(-1), 'http://local').searchParams.get('offset'), '0');
});
