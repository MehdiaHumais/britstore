path = 'templates/upload_app.html'
with open(path, encoding='utf-8', errors='replace') as f:
    s = f.read()

old = '''            {% if not is_edit %}
            <div class="form-section">
                <h3>Screenshots <span class="required-mark">*</span></h3>
                <p class="help-text">Upload at least <strong>7 screenshots</strong> (preferably all mobile, with tablet screenshots as a bonus). You can add more later on the edit page.</p>
                <div class="form-group">
                    <label>Mobile Screenshots <span class="required-mark">*</span></label>
                    <div class="file-input-wrap">
                        <input type="file" name="mobile_screenshots" id="mobileFiles" multiple accept="image/*" class="file-input" onchange="previewScreenshots(this, 'mobilePreviews')">
                        <label for="mobileFiles" class="file-input-label">Choose Files</label>
                        <span class="file-input-text" id="mobileFileText">No files chosen</span>
                    </div>
                    <small class="help-text">Select at least 7 mobile screenshots (hold Ctrl/Cmd to select multiple). Min width 320px.</small>
                    <div class="screenshot-previews" id="mobilePreviews"></div>
                </div>
                <div class="form-group">
                    <label>Tablet Screenshots</label>
                    <div class="file-input-wrap">
                        <input type="file" name="tablet_screenshots" id="tabletFiles" multiple accept="image/*" class="file-input" onchange="previewScreenshots(this, 'tabletPreviews')">
                        <label for="tabletFiles" class="file-input-label">Choose Files</label>
                        <span class="file-input-text" id="tabletFileText">No files chosen</span>
                    </div>
                    <small class="help-text">Optional ??" upload tablet screenshots here. Min width 600px.</small>
                    <div class="screenshot-previews" id="tabletPreviews"></div>
                </div>
            </div>
            {% endif %}'''

# try with different char
old2 = old.replace('\ufffd', '')

if old in s:
    s = s.replace(old, new_section) if False else None
# easier
s2 = s.replace('id="screenshotSection"', 'TEMP')
# just replace block
pass
