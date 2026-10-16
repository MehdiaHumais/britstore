path = 'templates/upload_app.html'
with open(path, encoding='utf-8', errors='replace') as f:
    s = f.read()
new_block = '''            {% if not is_edit %}
            <div class="form-section" id="screenshotSection">
                <h3>Screenshots <span class="required-mark">*</span></h3>
                <p class="help-text" id="screenshotHelp">Upload at least <strong>7 screenshots</strong> for Android apps.</p>
                <div class="form-group" id="mobileScreenshotsGroup">
                    <label>Mobile Screenshots <span class="required-mark">*</span></label>
                    <div class="file-input-wrap">
                        <input type="file" name="mobile_screenshots" id="mobileFiles" multiple accept="image/*" class="file-input" onchange="previewScreenshots(this, 'mobilePreviews')">
                        <label for="mobileFiles" class="file-input-label">Choose Files</label>
                        <span class="file-input-text" id="mobileFileText">No files chosen</span>
                    </div>
                    <small class="help-text">Select at least 7 mobile screenshots (hold Ctrl/Cmd to select multiple). Min width 320px.</small>
                    <div class="screenshot-previews" id="mobilePreviews"></div>
                </div>
                <div class="form-group" id="tabletScreenshotsGroup">
                    <label>Tablet Screenshots</label>
                    <div class="file-input-wrap">
                        <input type="file" name="tablet_screenshots" id="tabletFiles" multiple accept="image/*" class="file-input" onchange="previewScreenshots(this, 'tabletPreviews')">
                        <label for="tabletFiles" class="file-input-label">Choose Files</label>
                        <span class="file-input-text" id="tabletFileText">No files chosen</span>
                    </div>
                    <small class="help-text">Optional - upload tablet screenshots here. Min width 600px.</small>
                    <div class="screenshot-previews" id="tabletPreviews"></div>
                </div>
                <div class="form-group" id="desktopScreenshotsGroup" style="display:none">
                    <label>Desktop Screenshots <span class="required-mark">*</span></label>
                    <div class="file-input-wrap">
                        <input type="file" name="desktop_screenshots" id="desktopFiles" multiple accept="image/*" class="file-input" onchange="previewScreenshots(this, 'desktopPreviews')">
                        <label for="desktopFiles" class="file-input-label">Choose Files</label>
                        <span class="file-input-text" id="desktopFileText">No files chosen</span>
                    </div>
                    <small class="help-text">Upload desktop app screenshots (recommended: 5-7 screenshots showing main UI).</small>
                    <div class="screenshot-previews" id="desktopPreviews"></div>
                </div>
            </div>
            {% endif %}'''
start = s.find('{% if not is_edit %}')
end = s.find('<div class="form-actions">')
if start >= 0 and end > start:
    s2 = s[:start] + new_block + '\n\n            ' + s[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s2)
    print('ok')
else:
    print('no')
