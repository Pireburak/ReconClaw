"use strict";
(() => {
    const $ = id => document.getElementById(id);
    $('themeBtn').addEventListener('click', () => window.RCTheme.toggle());
    $('capTabs').addEventListener('click', event => {
        const button = event.target.closest('[data-ftab]');
        if (!button) return;
        document.querySelectorAll('#capTabs [data-ftab]').forEach(tab => {
            const active = tab === button;
            tab.classList.toggle('on', active);
            tab.setAttribute('aria-selected', String(active));
        });
        document.querySelectorAll('.cap-list').forEach(list => { list.hidden = list.dataset.fpanel !== button.dataset.ftab; });
    });
    const error = message => {
        $('formError').textContent = message;
        $('formError').hidden = !message;
    };
    async function post(url, body) {
        const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'İşlem tamamlanamadı. Tekrar deneyin.');
        return data;
    }
    $('verificationForm').addEventListener('submit', async event => {
        event.preventDefault();
        const code = $('verificationCode').value.trim();
        if (!/^[0-9]{6}$/.test(code)) return error('6 haneli doğrulama kodunu girin.');
        const body = {code};
        const password = document.querySelector('[data-verification-password]');
        if (password) {
            if (password.value.length < 8) return error('Parola en az 8 karakter olmalı.');
            body.password = password.value;
        }
        error('');
        $('verifyButton').disabled = true;
        try {
            await post('/auth/email/verify', body);
            window.location.href = '/';
        } catch (err) {
            error(err.message);
            $('verifyButton').disabled = false;
        }
    });
    $('resendButton').addEventListener('click', async () => {
        error('');
        $('formOk').hidden = true;
        $('resendButton').disabled = true;
        try {
            const data = await post('/auth/email/resend', {});
            $('verificationCode').value = '';
            $('formOk').textContent = data.message;
            $('formOk').hidden = false;
            $('verificationCode').focus();
            let remaining = 60;
            $('resendButton').textContent = `Yeni kod için ${remaining} saniye`;
            const timer = setInterval(() => {
                remaining--;
                $('resendButton').textContent = remaining ? `Yeni kod için ${remaining} saniye` : 'YENİ KOD GÖNDER';
                if (!remaining) {
                    clearInterval(timer);
                    $('resendButton').disabled = false;
                }
            }, 1000);
        } catch (err) {
            error(err.message);
            $('resendButton').disabled = false;
        }
    });
})();
