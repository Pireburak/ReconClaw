const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function screen(script, handler, passwordField = null) {
    const elements = new Map();
    const get = id => {
        if (!elements.has(id)) elements.set(id, {value: '', checked: false, hidden: true, disabled: false,
            textContent: '', dataset: {}, style: {}, events: {}, focus() {},
            addEventListener(name, callback) { this.events[name] = callback; }});
        return elements.get(id);
    };
    let timer;
    const window = {location: {href: '', search: ''}, matchMedia: () => ({matches: true})};
    const context = vm.createContext({document: {getElementById: get, querySelector: () => passwordField, querySelectorAll: () => []},
        window, fetch: handler, setInterval: callback => { timer = callback; return 1; }, clearInterval() {}, setTimeout() {}});
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/js/' + script), 'utf8'), context);
    return {get, window, tick: () => timer()};
}

test('verification submits leading zeros intact and opens the app after success', async () => {
    let sent;
    const p = screen('email-verification.js', async (url, options) => {
        sent = {url, body: JSON.parse(options.body)};
        return {ok: true, json: async () => ({ok: true})};
    });
    p.get('verificationCode').value = '012345';
    await p.get('verificationForm').events.submit({preventDefault() {}});
    assert.deepEqual(sent, {url: '/auth/email/verify', body: {code: '012345'}});
    assert.equal(p.window.location.href, '/');
});

test('wrong codes show the server message and allow another attempt', async () => {
    const p = screen('email-verification.js', async () => ({ok: false, json: async () => ({detail: 'Kod geçersiz veya süresi dolmuş.'})}));
    p.get('verificationCode').value = '123456';
    await p.get('verificationForm').events.submit({preventDefault() {}});
    assert.match(p.get('formError').textContent, /Kod geçersiz/);
    assert.equal(p.get('verifyButton').disabled, false);
    assert.equal(p.window.location.href, '');
});

test('passwordless accounts submit their new password with the code', async () => {
    let body;
    const p = screen('email-verification.js', async (_, options) => {
        body = JSON.parse(options.body);
        return {ok: true, json: async () => ({ok: true})};
    }, {value: 'newpassword123'});
    p.get('verificationCode').value = '012345';
    await p.get('verificationForm').events.submit({preventDefault() {}});
    assert.deepEqual(body, {code: '012345', password: 'newpassword123'});
    assert.equal(p.window.location.href, '/');
});

test('resend clears the previous code and disables resend for sixty seconds', async () => {
    const p = screen('email-verification.js', async () => ({ok: true, json: async () => ({message: 'Yeni kod gönderildi.'})}));
    p.get('verificationCode').value = '123456';
    await p.get('resendButton').events.click();
    assert.equal(p.get('verificationCode').value, '');
    assert.equal(p.get('resendButton').disabled, true);
    for (let i = 0; i < 60; i++) p.tick();
    assert.equal(p.get('resendButton').disabled, false);
});

test('login routes pending verification to code entry even after mail delivery failure', async () => {
    const p = screen('login.js', async () => ({ok: false, status: 503,
        json: async () => ({verification_required: true, detail: 'E-posta gönderilemedi.'})}));
    p.get('email').value = 'member@example.com';
    p.get('password').value = 'parola123';
    await p.get('authForm').events.submit({preventDefault() {}});
    assert.equal(p.window.location.href, '/eposta-dogrula');
});
