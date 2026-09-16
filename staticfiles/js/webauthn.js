function base64urlToBytes(base64url) {
    var base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    var padding = 4 - base64.length % 4;
    if (padding !== 4) { base64 += '='.repeat(padding); }
    var binary = atob(base64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) { bytes[i] = binary.charCodeAt(i); }
    return bytes;
}

function bytesToBase64url(bytes) {
    var binary = '';
    for (var i = 0; i < bytes.length; i++) { binary += String.fromCharCode(bytes[i]); }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function fixOptions(options) {
    if (options.challenge) options.challenge = base64urlToBytes(options.challenge);
    if (options.user && options.user.id) options.user.id = base64urlToBytes(options.user.id);
    if (options.excludeCredentials) {
        options.excludeCredentials.forEach(function(c) { if (c.id) c.id = base64urlToBytes(c.id); });
    }
    if (options.allowCredentials) {
        options.allowCredentials.forEach(function(c) { if (c.id) c.id = base64urlToBytes(c.id); });
    }
    return options;
}

function credentialToJson(cred) {
    var resp = cred.response;
    var json = {
        id: cred.id,
        rawId: bytesToBase64url(new Uint8Array(cred.rawId)),
        type: cred.type,
        response: {}
    };
    if (resp.clientDataJSON) {
        json.response.clientDataJSON = bytesToBase64url(new Uint8Array(resp.clientDataJSON));
    }
    if (resp.attestationObject) {
        json.response.attestationObject = bytesToBase64url(new Uint8Array(resp.attestationObject));
    }
    if (resp.authenticatorData) {
        json.response.authenticatorData = bytesToBase64url(new Uint8Array(resp.authenticatorData));
    }
    if (resp.signature) {
        json.response.signature = bytesToBase64url(new Uint8Array(resp.signature));
    }
    if (resp.userHandle) {
        json.response.userHandle = bytesToBase64url(new Uint8Array(resp.userHandle));
    }
    if (resp.transports) {
        json.response.transports = resp.transports;
    }
    return json;
}

function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function supportsWebAuthn() {
    return window.PublicKeyCredential !== undefined;
}

function registerFingerprint() {
    return fetch('/webauthn/register/begin/')
        .then(function(r) { return r.json(); })
        .then(function(options) {
            fixOptions(options);
            return navigator.credentials.create({ publicKey: options });
        })
        .then(function(cred) {
            var json = credentialToJson(cred);
            return fetch('/webauthn/register/complete/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify(json),
            });
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === 'ok') {
                localStorage.setItem('fp_credential_id', data.credential_id);
                return data;
            }
            throw new Error(data.error || 'Registration failed');
        });
}

function loginFingerprint(credentialId) {
    return fetch('/webauthn/login/begin/?credential_id=' + encodeURIComponent(credentialId))
        .then(function(r) { return r.json(); })
        .then(function(options) {
            if (options.error) throw new Error(options.error);
            fixOptions(options);
            return navigator.credentials.get({ publicKey: options });
        })
        .then(function(cred) {
            var json = credentialToJson(cred);
            return fetch('/webauthn/login/complete/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify(json),
            });
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === 'ok') return data;
            throw new Error(data.error || 'Login failed');
        });
}

function getCSRFToken() {
    var name = 'csrftoken';
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : '';
}
