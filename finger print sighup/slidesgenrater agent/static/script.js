document.addEventListener("DOMContentLoaded", async () => {

    // =============================================
    // --- ELEMENT REFERENCES ---
    // =============================================
    const loginSection      = document.getElementById("login-section");
    const signupSection     = document.getElementById("signup-section");
    const settingsSection   = document.getElementById("settings-section");
    const mainHeader        = document.getElementById("main-header");
    const generatorForm     = document.getElementById("generator-form");

    const loginForm         = document.getElementById("login-form");
    const signupForm        = document.getElementById("signup-form");
    const settingsForm      = document.getElementById("settings-form");

    const switchToSignup    = document.getElementById("switch-to-signup");
    const switchToLogin     = document.getElementById("switch-to-login");
    const openSettingsBtn   = document.getElementById("open-settings-btn");
    const closeSettingsBtn  = document.getElementById("close-settings-btn");
    const logoutBtn         = document.getElementById("logout-btn");

    const userDisplayName   = document.getElementById("user-display-name");
    const userDisplayEmail  = document.getElementById("user-display-email");

    // Fingerprint elements
    const fingerprintLoginBtn     = document.getElementById("fingerprint-login-btn");
    const fingerprintSignupBtn    = document.getElementById("fingerprint-signup-btn");
    const fingerprintNameStep     = document.getElementById("fingerprint-name-step");
    const fingerprintSignupName   = document.getElementById("fingerprint-signup-name");
    const fingerprintNameConfirm  = document.getElementById("fingerprint-name-confirm-btn");
    const settingsEmailMode       = document.getElementById("settings-email-mode");
    const settingsFingerprintMode = document.getElementById("settings-fingerprint-mode");
    const settingsCreatePassForm  = document.getElementById("settings-create-pass-form");

    // Track what action the native scanner should perform after a successful scan
    let pendingFingerprintAction  = null; // 'login' or 'signup'

    // Generate or retrieve a unique ID for this device (stored in localStorage)
    function getDeviceId() {
        let id = localStorage.getItem('slidewiz_device_id');
        if (!id) {
            id = 'dev_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36);
            localStorage.setItem('slidewiz_device_id', id);
        }
        return id;
    }

    // =============================================
    // --- HELPER: SHOW/HIDE SECTIONS ---
    // =============================================
    function showApp(user) {
        // Hide all auth screens
        if (loginSection)   loginSection.classList.add("hidden");
        if (signupSection)  signupSection.classList.add("hidden");
        if (settingsSection) settingsSection.classList.add("hidden");

        // Show main app
        mainHeader.classList.remove("hidden");
        generatorForm.classList.remove("hidden");

        // Populate profile bar
        if (userDisplayName)  userDisplayName.innerText = user.name;
        // Show email OR fingerprint indicator
        if (userDisplayEmail) {
            userDisplayEmail.innerText = user.is_fingerprint ? '🔒 Fingerprint Account' : user.email;
        }
    }

    function showLogin() {
        if (loginSection)   loginSection.classList.remove("hidden");
        if (signupSection)  signupSection.classList.add("hidden");
        if (settingsSection) settingsSection.classList.add("hidden");
        mainHeader.classList.add("hidden");
        generatorForm.classList.add("hidden");
    }

    function showSignup() {
        if (loginSection)   loginSection.classList.add("hidden");
        if (signupSection)  signupSection.classList.remove("hidden");
        if (settingsSection) settingsSection.classList.add("hidden");
        mainHeader.classList.add("hidden");
        generatorForm.classList.add("hidden");
    }

    function showSettings(user) {
        if (loginSection)   loginSection.classList.add("hidden");
        if (signupSection)  signupSection.classList.add("hidden");
        settingsSection.classList.remove("hidden");
        mainHeader.classList.add("hidden");
        generatorForm.classList.add("hidden");

        // Show the correct settings panel based on account type
        if (user && user.is_fingerprint) {
            if (settingsEmailMode)       settingsEmailMode.classList.add("hidden");
            if (settingsFingerprintMode) settingsFingerprintMode.classList.remove("hidden");
        } else {
            if (settingsEmailMode)       settingsEmailMode.classList.remove("hidden");
            if (settingsFingerprintMode) settingsFingerprintMode.classList.add("hidden");
            if (settingsForm) settingsForm.reset();
        }
    }

    // =============================================
    // --- SESSION CHECK ON PAGE LOAD ---
    // =============================================
    let currentUser = null; // Keep track of logged-in user globally
    try {
        const res = await fetch('/api/me');
        const data = await res.json();
        if (data.logged_in) {
            currentUser = data.user;
            showApp(data.user);
        } else {
            showLogin();
        }
    } catch (e) {
        showLogin();
    }

    // =============================================
    // --- SWITCH BETWEEN LOGIN & SIGNUP ---
    // =============================================
    if (switchToSignup) {
        switchToSignup.addEventListener("click", (e) => {
            e.preventDefault();
            showSignup();
        });
    }
    if (switchToLogin) {
        switchToLogin.addEventListener("click", (e) => {
            e.preventDefault();
            showLogin();
        });
    }

    // =============================================
    // --- FINGERPRINT AUTH FLOW ---
    // =============================================

    // Called by Android Java after a SUCCESSFUL fingerprint scan
    window.onNativeFingerprintSuccess = async () => {
        const deviceId = getDeviceId();

        if (pendingFingerprintAction === 'signup') {
            // Show the name entry step
            if (fingerprintNameStep) fingerprintNameStep.classList.remove("hidden");
            if (fingerprintSignupBtn) fingerprintSignupBtn.style.display = 'none';

        } else if (pendingFingerprintAction === 'login') {
            // Attempt fingerprint login immediately
            try {
                const res = await fetch('/api/fingerprint', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: deviceId, action: 'login' })
                });
                const result = await res.json();
                if (result.success) {
                    currentUser = result.user;
                    showApp(result.user);
                } else {
                    alert(result.error || 'No fingerprint account found. Please sign up first.');
                }
            } catch (err) {
                alert('Network error. Please try again.');
            }
        }
        pendingFingerprintAction = null;
    };

    // Called by Android Java after a FAILED fingerprint scan
    window.onNativeFingerprintFailed = () => {
        pendingFingerprintAction = null;
        alert('Fingerprint not recognized. Please try again.');
    };

    // Helper: triggers the native scanner OR simulates it in the browser
    function triggerFingerprint(action) {
        pendingFingerprintAction = action;
        if (window.AndroidBridge && window.AndroidBridge.startFingerprint) {
            window.AndroidBridge.startFingerprint();
        } else {
            // Simulate for browser testing
            setTimeout(() => window.onNativeFingerprintSuccess(), 1200);
        }
    }

    // --- FINGERPRINT LOGIN BUTTON ---
    if (fingerprintLoginBtn) {
        fingerprintLoginBtn.addEventListener('click', () => {
            triggerFingerprint('login');
        });
    }

    // --- FINGERPRINT SIGNUP BUTTON ---
    if (fingerprintSignupBtn) {
        fingerprintSignupBtn.addEventListener('click', () => {
            triggerFingerprint('signup');
        });
    }

    // --- FINGERPRINT SIGNUP: NAME CONFIRMATION ---
    if (fingerprintNameConfirm) {
        fingerprintNameConfirm.addEventListener('click', async () => {
            const name = fingerprintSignupName ? fingerprintSignupName.value.trim() : '';
            if (!name) {
                alert('Please enter your name.');
                return;
            }
            const deviceId = getDeviceId();
            const btn = fingerprintNameConfirm;
            btn.disabled = true;
            btn.querySelector('.btn-text').innerText = 'Creating...';

            try {
                const res = await fetch('/api/fingerprint', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: deviceId, name: name, action: 'signup' })
                });
                const result = await res.json();
                if (result.success) {
                    currentUser = result.user;
                    showApp(result.user);
                } else {
                    alert(result.error || 'Signup failed.');
                    // Reset the UI
                    if (fingerprintNameStep) fingerprintNameStep.classList.add("hidden");
                    if (fingerprintSignupBtn) fingerprintSignupBtn.style.display = '';
                }
            } catch (err) {
                alert('Network error. Please try again.');
            } finally {
                btn.disabled = false;
                btn.querySelector('.btn-text').innerText = 'Complete Sign Up';
            }
        });
    }


    // =============================================
    // --- LOGIN FORM SUBMIT ---
    // =============================================
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email    = document.getElementById("login-email").value.trim();
            const password = document.getElementById("login-password").value;
            const btn      = loginForm.querySelector("button[type='submit']");
            const original = btn.innerHTML;

            btn.innerHTML  = '<span class="btn-text">Logging in...</span>';
            btn.disabled   = true;

            try {
                const res    = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const result = await res.json();

                if (result.success) {
                    showApp(result.user);
                } else {
                    showError(loginForm, result.error || "Login failed.");
                }
            } catch (err) {
                showError(loginForm, "Network error. Please try again.");
            } finally {
                btn.innerHTML = original;
                btn.disabled  = false;
            }
        });
    }

    // =============================================
    // --- SIGNUP FORM SUBMIT ---
    // =============================================
    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name     = document.getElementById("signup-name").value.trim();
            const email    = document.getElementById("signup-email").value.trim();
            const password = document.getElementById("signup-password").value;
            const btn      = signupForm.querySelector("button[type='submit']");
            const original = btn.innerHTML;

            btn.innerHTML  = '<span class="btn-text">Creating account...</span>';
            btn.disabled   = true;

            try {
                const res    = await fetch('/api/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });
                const result = await res.json();

                if (result.success) {
                    showApp(result.user);
                } else {
                    showError(signupForm, result.error || "Signup failed.");
                }
            } catch (err) {
                showError(signupForm, "Network error. Please try again.");
            } finally {
                btn.innerHTML = original;
                btn.disabled  = false;
            }
        });
    }

    // =============================================
    // --- LOGOUT ---
    // =============================================
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            await fetch('/api/logout', { method: 'POST' });
            showLogin();
        });
    }

    // =============================================
    // --- SETTINGS (Change Password) ---
    // =============================================
    if (openSettingsBtn) {
        openSettingsBtn.addEventListener("click", () => showSettings(currentUser));
    }
    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener("click", () => {
            settingsSection.classList.add("hidden");
            mainHeader.classList.remove("hidden");
            generatorForm.classList.remove("hidden");
        });
    }

    if (settingsForm) {
        settingsForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const currentPw = document.getElementById("current-password").value;
            const newPw     = document.getElementById("new-password").value;
            const btn       = settingsForm.querySelector("button[type='submit']");
            const original  = btn.innerHTML;

            btn.innerHTML = '<span class="btn-text">Saving...</span>';
            btn.disabled  = true;

            try {
                const res    = await fetch('/api/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ current_password: currentPw, new_password: newPw })
                });
                const result = await res.json();

                if (result.success) {
                    showSuccess(settingsForm, "Password updated successfully!");
                    settingsForm.reset();
                    setTimeout(() => {
                        settingsSection.classList.add("hidden");
                        mainHeader.classList.remove("hidden");
                        generatorForm.classList.remove("hidden");
                    }, 1500);
                } else {
                    showError(settingsForm, result.error || "Failed to update password.");
                }
            } catch (err) {
                showError(settingsForm, "Network error. Please try again.");
            } finally {
                btn.innerHTML = original;
                btn.disabled  = false;
            }
        });
    }

    // --- FINGERPRINT USERS: Save Backup Password ---
    // This requires fingerprint verification first!
    let pendingBackupEmail = '';
    let pendingBackupPass  = '';

    // Called after fingerprint verification succeeds for password creation
    window.onBackupFingerprintSuccess = async () => {
        const btn     = settingsCreatePassForm.querySelector("button[type='submit']");
        const original = btn.innerHTML;
        btn.innerHTML = '<span class="btn-text">Saving...</span>';
        btn.disabled  = true;

        try {
            const res = await fetch('/api/fingerprint-set-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: pendingBackupEmail, new_password: pendingBackupPass })
            });
            const result = await res.json();
            if (result.success) {
                showSuccess(settingsCreatePassForm, 'Backup password saved! You can now login with email too.');
                if (currentUser) currentUser.is_fingerprint = false;
                settingsCreatePassForm.reset();
                // Switch settings back to normal "Change Password" mode after a delay
                setTimeout(() => {
                    if (settingsEmailMode)       settingsEmailMode.classList.remove("hidden");
                    if (settingsFingerprintMode) settingsFingerprintMode.classList.add("hidden");
                    settingsSection.classList.add("hidden");
                    mainHeader.classList.remove("hidden");
                    generatorForm.classList.remove("hidden");
                }, 2000);
            } else {
                showError(settingsCreatePassForm, result.error || 'Failed to save password.');
            }
        } catch (err) {
            showError(settingsCreatePassForm, 'Network error. Please try again.');
        } finally {
            btn.innerHTML = original;
            btn.disabled  = false;
            pendingBackupEmail = '';
            pendingBackupPass  = '';
        }
    };

    window.onBackupFingerprintFailed = () => {
        const btn = settingsCreatePassForm.querySelector("button[type='submit']");
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">Save Backup Password</span><i class="ph-bold ph-floppy-disk"></i>';
        showError(settingsCreatePassForm, 'Fingerprint verification failed. Please try again.');
        pendingBackupEmail = '';
        pendingBackupPass  = '';
    };

    if (settingsCreatePassForm) {
        settingsCreatePassForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email   = document.getElementById('fp-new-email').value.trim();
            const newPass = document.getElementById('fp-new-password').value;

            if (!email || !newPass) {
                showError(settingsCreatePassForm, 'Email and password are required.');
                return;
            }
            if (newPass.length < 6) {
                showError(settingsCreatePassForm, 'Password must be at least 6 characters.');
                return;
            }

            // Store values temporarily, then verify fingerprint
            pendingBackupEmail = email;
            pendingBackupPass  = newPass;

            const btn = settingsCreatePassForm.querySelector("button[type='submit']");
            btn.innerHTML = '<span class="btn-text">Verify fingerprint...</span>';
            btn.disabled  = true;

            // Override the global callbacks temporarily for this action
            const origSuccess = window.onNativeFingerprintSuccess;
            const origFailed  = window.onNativeFingerprintFailed;
            window.onNativeFingerprintSuccess = () => {
                // Restore original callbacks
                window.onNativeFingerprintSuccess = origSuccess;
                window.onNativeFingerprintFailed  = origFailed;
                window.onBackupFingerprintSuccess();
            };
            window.onNativeFingerprintFailed = () => {
                window.onNativeFingerprintSuccess = origSuccess;
                window.onNativeFingerprintFailed  = origFailed;
                window.onBackupFingerprintFailed();
            };

            // Trigger the native fingerprint scanner
            if (window.AndroidBridge && window.AndroidBridge.startFingerprint) {
                window.AndroidBridge.startFingerprint();
            } else {
                // Simulate for browser testing
                setTimeout(() => window.onNativeFingerprintSuccess(), 1200);
            }
        });
    }

    // =============================================
    // --- INLINE ERROR/SUCCESS MESSAGES ---
    // =============================================
    function showError(form, message) {
        clearMessages(form);
        const el = document.createElement("p");
        el.className = "form-feedback error-msg";
        el.innerText = "⚠ " + message;
        el.style.cssText = "color: var(--secondary); font-weight:600; text-align:center; margin-top:12px; animation: fadeIn 0.3s ease;";
        form.appendChild(el);
        setTimeout(() => el.remove(), 5000);
    }

    function showSuccess(form, message) {
        clearMessages(form);
        const el = document.createElement("p");
        el.className = "form-feedback success-msg";
        el.innerText = "✓ " + message;
        el.style.cssText = "color: #10B981; font-weight:600; text-align:center; margin-top:12px; animation: fadeIn 0.3s ease;";
        form.appendChild(el);
    }

    function clearMessages(form) {
        form.querySelectorAll(".form-feedback").forEach(el => el.remove());
    }

    // =============================================
    // --- SLIDE GENERATOR LOGIC ---
    // =============================================
    const form         = document.getElementById("generator-form");
    const loadingState = document.getElementById("loading-state");
    const successState = document.getElementById("success-state");
    const errorState   = document.getElementById("error-state");
    const downloadBtn  = document.getElementById("download-btn");
    const resetBtn     = document.getElementById("reset-btn");
    const retryBtn     = document.getElementById("retry-btn");
    const errorMessage = document.getElementById("error-message");
    const statusText   = document.querySelector(".status-text");

    const subtopicsInput        = document.getElementById("subtopics");
    const subtopicsBehaviorGroup= document.getElementById("subtopics_behavior_group");
    const documentInput         = document.getElementById("file-upload-input");
    const pdfImagesGroup        = document.getElementById("pdf_images_group");
    const smartCount            = document.getElementById("smart_count");
    const smartCountContainer   = document.getElementById("smart_count_container");
    const slideCountGroup       = document.getElementById("slide_count_group");

    if (documentInput) {
        documentInput.addEventListener("change", () => {
            const file    = documentInput.files[0];
            const hasFile = !!file;
            const isPdf   = hasFile && file.name.toLowerCase().endsWith(".pdf");
            const display = document.getElementById("file-name-display");
            if (display) display.innerText = hasFile ? file.name : "Select File...";
            if (pdfImagesGroup) pdfImagesGroup.classList.toggle("hidden", !isPdf);
            if (!isPdf && document.getElementById("extract_pdf_images")) {
                document.getElementById("extract_pdf_images").checked = false;
            }
            if (smartCountContainer) {
                if (hasFile) {
                    smartCountContainer.classList.remove("hidden");
                    smartCountContainer.style.display = "flex";
                } else {
                    smartCountContainer.classList.add("hidden");
                    smartCountContainer.style.display = "none";
                    if (smartCount) smartCount.checked = false;
                    if (slideCountGroup) { slideCountGroup.style.opacity = "1"; slideCountGroup.style.pointerEvents = "all"; }
                }
            }
        });
    }

    if (smartCount) {
        smartCount.addEventListener("change", () => {
            if (slideCountGroup) {
                slideCountGroup.style.opacity = smartCount.checked ? "0.5" : "1";
                slideCountGroup.style.pointerEvents = smartCount.checked ? "none" : "all";
            }
        });
    }

    if (subtopicsInput) {
        subtopicsInput.addEventListener("input", () => {
            if (subtopicsBehaviorGroup) subtopicsBehaviorGroup.classList.toggle("hidden", subtopicsInput.value.trim().length === 0);
        });
    }

    const loadingMessages = [
        "The AI is structurally analyzing the topic...",
        "Drafting professional content...",
        "Structuring PowerPoint outlines...",
        "Designing native vector graphics...",
        "Applying your selected theme...",
        "Finalizing the .pptx file..."
    ];

    function showState(stateElement) {
        if (!stateElement) return;
        form.classList.add("hidden");
        loadingState.classList.add("hidden");
        successState.classList.add("hidden");
        errorState.classList.add("hidden");
        stateElement.classList.remove("hidden");
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            formData.set("include_images", document.getElementById("include_images").checked);
            formData.set("extract_pdf_images", document.getElementById("extract_pdf_images").checked);
            formData.set("smart_count", smartCount.checked);
            if (!formData.get("topic").trim() && !formData.get("document").name) return;

            showState(loadingState);
            let messageIdx = 0;
            const msgInterval = setInterval(() => {
                messageIdx = (messageIdx + 1) % loadingMessages.length;
                statusText.innerText = loadingMessages[messageIdx];
                statusText.style.animation = 'none';
                statusText.offsetHeight;
                statusText.style.animation = 'fadeIn 0.5s ease';
            }, 3000);

            try {
                const response = await fetch('/generate', { method: 'POST', body: formData });
                const result   = await response.json();
                if (!response.ok || result.error) throw new Error(result.error || "Server rejected request.");

                const taskId = result.task_id;
                while (true) {
                    await new Promise(r => setTimeout(r, 4000));
                    const statRes  = await fetch(`/status/${taskId}`);
                    const statData = await statRes.json();
                    if (statData.progress_text) statusText.innerText = statData.progress_text;
                    if (statData.status === "error") throw new Error(statData.error);
                    if (statData.status === "done") {
                        clearInterval(msgInterval);
                        downloadBtn.href = statData.download_url;
                        showState(successState);
                        break;
                    }
                }
            } catch (error) {
                clearInterval(msgInterval);
                errorMessage.innerText = error.message;
                showState(errorState);
            }
        });
    }

    // --- Custom Select Dropdown ---
    const setupCustomSelect = (containerId) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        const trigger = container.querySelector(".select-trigger");
        const options = container.querySelectorAll(".option");
        const hiddenInput = container.querySelector("input[type='hidden']");
        const selectedValueDisplay = container.querySelector(".selected-value");

        trigger.addEventListener("click", (e) => {
            e.stopPropagation();
            document.querySelectorAll(".custom-select").forEach(s => { if (s !== container) s.classList.remove("active"); });
            container.classList.toggle("active");
        });

        options.forEach(opt => {
            opt.addEventListener("click", () => {
                hiddenInput.value = opt.getAttribute("data-value");
                selectedValueDisplay.innerText = opt.innerText;
                options.forEach(o => o.classList.remove("selected"));
                opt.classList.add("selected");
                container.classList.remove("active");
                hiddenInput.dispatchEvent(new Event("change"));
            });
        });
    };

    setupCustomSelect("select-detail_level");
    setupCustomSelect("select-theme");

    document.addEventListener("click", () => {
        document.querySelectorAll(".custom-select").forEach(s => s.classList.remove("active"));
    });

    if (resetBtn) resetBtn.addEventListener("click", () => showState(form));
    if (retryBtn) retryBtn.addEventListener("click", () => showState(form));
});
