#!/usr/bin/env python3
"""Build el-CRM Product Bible single-page HTML from markdown files."""

import re
import os
import html as html_mod

BASE = '/tmp/web-assets/el_crm'

# Nav items: (id, label, source)
NAV_ITEMS = [
    ('overview', 'Overview', '00-product-overview.md'),
    ('user-flows', 'User Flows', '01-user-flows/'),
    ('features', 'Feature Inventory', '02-feature-inventory.md'),
    ('info-arch', 'Information Architecture', '03-information-architecture.md'),
    ('page-specs', 'Page Specs', '04-page-specs/'),
    ('data-model', 'Data Model', '05-data-model.md'),
    ('api', 'API Contracts', '06-api-contracts.md'),
    ('integration', 'Integration Map', '07-integration-map.md'),
    ('rbac', 'RBAC Matrix', '08-rbac-matrix.md'),
    ('workflow', 'Workflow Engine', '09-workflow-engine.md'),
    ('channels', 'Channel Specs', '10-channel-specs.md'),
    ('reports', 'Report Specs', '11-report-specs.md'),
    ('config', 'Configuration', '12-configuration-spec.md'),
    ('channel-integration', 'Channel Integration', '13-channel-integration-guide.md'),
]

USER_FLOW_FILES = [
    ('00-overview.md', 'Overview'),
    ('01-agent-daily-workflow.md', 'Agent Daily Workflow'),
    ('02-inbound-message.md', 'Inbound Message'),
    ('03-outbound-reach-out.md', 'Outbound Reach-Out'),
    ('04-lead-qualification.md', 'Lead Qualification'),
    ('05-pipeline-management.md', 'Pipeline Management'),
    ('06-follow-up-workflow.md', 'Follow-Up Workflow'),
    ('07-contact-account-management.md', 'Contact & Account Mgmt'),
    ('08-manager-dashboard.md', 'Manager Dashboard'),
    ('09-report-generation.md', 'Report Generation'),
    ('10-assignment-override.md', 'Assignment Override'),
    ('11-pipeline-review.md', 'Pipeline Review'),
    ('12-workspace-setup.md', 'Workspace Setup'),
    ('13-user-role-management.md', 'User & Role Mgmt'),
    ('14-workflow-configuration.md', 'Workflow Configuration'),
    ('15-channel-configuration.md', 'Channel Configuration'),
    ('16-first-time-login.md', 'First-Time Login'),
    ('17-search-and-filters.md', 'Search & Filters'),
    ('18-notifications.md', 'Notifications'),
]

PAGE_SPEC_FILES = [
    ('00-overview.md', 'Overview'),
    ('01-inbox.md', 'Inbox'),
    ('02-contact-list.md', 'Contact List'),
    ('03-contact-detail.md', 'Contact Detail'),
    ('04-account-list.md', 'Account List'),
    ('05-account-detail.md', 'Account Detail'),
    ('06-pipeline.md', 'Pipeline Board'),
    ('07-follow-ups.md', 'Follow-Ups'),
    ('08-dashboard.md', 'Dashboard'),
    ('09-reports.md', 'Reports'),
    ('10-settings.md', 'Settings'),
]


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def escape(text):
    return html_mod.escape(text)


def convert_inline(text):
    """Convert inline markdown: bold, italic, code, links."""
    # Code spans first (protect from other transforms)
    parts = []
    i = 0
    code_pattern = re.compile(r'`([^`]+)`')
    last = 0
    for m in code_pattern.finditer(text):
        parts.append(text[last:m.start()])
        parts.append(f'<code>{escape(m.group(1))}</code>')
        last = m.end()
    parts.append(text[last:])
    text = ''.join(parts)

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Status tags
    text = re.sub(r'\[Core\]', '<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:4px;font-size:11px;">Core</span>', text)
    text = re.sub(r'\[Enhanced\]', '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:11px;">Enhanced</span>', text)
    text = re.sub(r'\[Future\]', '<span style="background:#8197c0;color:white;padding:2px 8px;border-radius:4px;font-size:11px;">Future</span>', text)
    return text


def md_to_html(md_text, section_counter_start=1):
    """Convert markdown text to styled HTML sections."""
    lines = md_text.split('\n')
    out = []
    i = 0
    section_num = section_counter_start
    in_section = False
    in_table = False
    in_code = False
    code_lines = []
    in_list = False
    in_blockquote = False
    bq_lines = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append('</ul>')
            in_list = False

    def close_blockquote():
        nonlocal in_blockquote, bq_lines
        if in_blockquote:
            content = '<br>'.join(convert_inline(l) for l in bq_lines)
            out.append(f'<div class="info-box">{content}</div>')
            bq_lines = []
            in_blockquote = False

    def close_table():
        nonlocal in_table
        if in_table:
            out.append('</tbody></table>')
            in_table = False

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                # End code block
                close_list()
                close_blockquote()
                content = escape('\n'.join(code_lines))
                out.append(f'<pre style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto;font-family:monospace;font-size:12px;line-height:1.5;margin:16px 0;">{content}</pre>')
                code_lines = []
                in_code = False
            else:
                close_list()
                close_blockquote()
                close_table()
                in_code = True
                code_lines = []
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Skip the first H1 title (already shown in panel header)
        if stripped.startswith('# ') and not stripped.startswith('## '):
            close_list()
            close_blockquote()
            close_table()
            i += 1
            continue

        # Horizontal rules
        if stripped == '---' or stripped == '***' or stripped == '___':
            close_list()
            close_blockquote()
            close_table()
            if in_section:
                out.append('</div>')  # close section
                in_section = False
            i += 1
            continue

        # H2 -> section
        if stripped.startswith('## '):
            close_list()
            close_blockquote()
            close_table()
            if in_section:
                out.append('</div>')
            title = convert_inline(stripped[3:])
            out.append(f'<div class="section">')
            out.append(f'<div class="section-header"><div class="section-num">{section_num}</div><div class="section-title">{title}</div></div>')
            section_num += 1
            in_section = True
            i += 1
            continue

        # H3 -> sub-heading
        if stripped.startswith('### '):
            close_list()
            close_blockquote()
            close_table()
            title = convert_inline(stripped[4:])
            out.append(f'<h3 style="font-size:15px;font-weight:600;color:var(--primary-dark);margin:18px 0 10px 0;">{title}</h3>')
            i += 1
            continue

        # H4 -> sub-sub-heading
        if stripped.startswith('#### '):
            close_list()
            close_blockquote()
            close_table()
            title = convert_inline(stripped[5:])
            out.append(f'<h4 style="font-size:14px;font-weight:600;color:var(--text);margin:14px 0 8px 0;">{title}</h4>')
            i += 1
            continue

        # H5
        if stripped.startswith('##### '):
            close_list()
            close_blockquote()
            close_table()
            title = convert_inline(stripped[6:])
            out.append(f'<h5 style="font-size:13px;font-weight:600;color:var(--text-light);margin:12px 0 6px 0;">{title}</h5>')
            i += 1
            continue

        # Blockquote
        if stripped.startswith('> '):
            close_list()
            close_table()
            bq_lines.append(stripped[2:])
            in_blockquote = True
            i += 1
            continue
        elif in_blockquote and stripped == '':
            close_blockquote()
            i += 1
            continue
        elif in_blockquote and not stripped.startswith('>'):
            close_blockquote()
            # Don't increment, re-process this line

        # Table
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            close_list()
            close_blockquote()
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            # Check if separator row
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue
            if not in_table:
                # Start table - this is header row
                out.append('<table><thead><tr>')
                for c in cells:
                    out.append(f'<th>{convert_inline(c)}</th>')
                out.append('</tr></thead><tbody>')
                in_table = True
            else:
                out.append('<tr>')
                for c in cells:
                    out.append(f'<td>{convert_inline(c)}</td>')
                out.append('</tr>')
            i += 1
            continue
        else:
            close_table()

        # Unordered list
        if re.match(r'^[\s]*[-*] ', stripped):
            close_blockquote()
            close_table()
            indent_match = re.match(r'^(\s*)', line)
            indent = len(indent_match.group(1)) if indent_match else 0
            content = re.sub(r'^[\s]*[-*] ', '', line).strip()
            if not in_list:
                out.append('<ul style="margin:8px 0;padding-left:20px;font-size:13px;color:var(--text-light);">')
                in_list = True
            out.append(f'<li style="margin-bottom:4px;">{convert_inline(content)}</li>')
            i += 1
            continue

        # Ordered list
        if re.match(r'^[\s]*\d+\. ', stripped):
            close_blockquote()
            close_table()
            content = re.sub(r'^[\s]*\d+\. ', '', line).strip()
            if not in_list:
                out.append('<ul style="margin:8px 0;padding-left:20px;font-size:13px;color:var(--text-light);list-style-type:decimal;">')
                in_list = True
            out.append(f'<li style="margin-bottom:4px;">{convert_inline(content)}</li>')
            i += 1
            continue

        # Not a list item
        close_list()

        # Empty line
        if stripped == '':
            close_blockquote()
            i += 1
            continue

        # Regular paragraph
        close_blockquote()
        out.append(f'<p style="color:var(--text-light);font-size:13px;margin-bottom:10px;">{convert_inline(stripped)}</p>')
        i += 1

    # Close any open elements
    close_list()
    close_blockquote()
    close_table()
    if in_code:
        content = escape('\n'.join(code_lines))
        out.append(f'<pre style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto;font-family:monospace;font-size:12px;line-height:1.5;margin:16px 0;">{content}</pre>')
    if in_section:
        out.append('</div>')

    return '\n'.join(out)


def build_sub_nav_panel(panel_id, files, base_dir):
    """Build a panel with sub-navigation tabs."""
    tabs_html = []
    content_html = []

    for idx, (fname, label) in enumerate(files):
        tab_id = f'{panel_id}-sub-{idx}'
        active = 'active' if idx == 0 else ''
        tabs_html.append(f'<button class="sub-nav-item {active}" onclick="showSubTab(\'{panel_id}\', \'{tab_id}\', this)">{label}</button>')

        fpath = os.path.join(base_dir, fname)
        md = read_file(fpath)
        html_content = md_to_html(md)
        display = 'block' if idx == 0 else 'none'
        content_html.append(f'<div class="sub-panel" id="{tab_id}" style="display:{display};">{html_content}</div>')

    return f'''<div class="sub-nav" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px;padding:12px;background:var(--bg);border-radius:10px;">
{''.join(tabs_html)}
</div>
{''.join(content_html)}'''


def build_html():
    # Build nav
    nav_html = []
    for idx, (nav_id, label, _) in enumerate(NAV_ITEMS):
        active = ' active' if idx == 0 else ''
        nav_html.append(f'<button class="nav-item{active}" onclick="showTab(\'{nav_id}\', this)"><span class="nav-num">{idx}</span>{label}</button>')

    # Build panels
    panels_html = []
    for idx, (nav_id, label, source) in enumerate(NAV_ITEMS):
        active = ' active' if idx == 0 else ''

        if nav_id == 'user-flows':
            inner = build_sub_nav_panel('uf', USER_FLOW_FILES, os.path.join(BASE, '01-user-flows'))
        elif nav_id == 'page-specs':
            inner = build_sub_nav_panel('ps', PAGE_SPEC_FILES, os.path.join(BASE, '04-page-specs'))
        else:
            fpath = os.path.join(BASE, source)
            md = read_file(fpath)
            inner = md_to_html(md)

        panels_html.append(f'<div class="panel{active}" id="{nav_id}">\n<h2 style="font-size:22px;font-weight:700;color:var(--primary-dark);margin-bottom:20px;">{label}</h2>\n{inner}\n</div>')

    css = read_file('/tmp/web-assets/products.html')
    # Extract CSS between <style> and </style>
    css_match = re.search(r'<style>(.*?)</style>', css, re.DOTALL)
    css_content = css_match.group(1) if css_match else ''

    # Add sub-nav styles
    extra_css = """
        .sub-nav-item {
            padding: 8px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--white);
            color: var(--text-light);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .sub-nav-item:hover {
            background: var(--primary-lighter);
            color: var(--primary-dark);
            border-color: var(--primary-light);
        }
        .sub-nav-item.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        pre {
            white-space: pre;
            overflow-x: auto;
        }
        code {
            background: var(--bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'SF Mono', 'Fira Code', monospace;
        }
        a {
            color: var(--primary-dark);
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        @media (max-width: 600px) {
            .sub-nav-item {
                padding: 6px 10px;
                font-size: 11px;
            }
        }
    """

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>el-CRM Product Bible</title>
    <style>
{css_content}
{extra_css}
    </style>
</head>
<body>
    <button class="mobile-menu-toggle" onclick="toggleMobileMenu()" id="menuToggle">☰</button>
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeMobileMenu()"></div>

    <div class="layout">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h1>el-CRM</h1>
                <p>Product Bible</p>
            </div>
            <div class="nav">
                {''.join(nav_html)}
            </div>
        </div>

        <div class="content">
            {''.join(panels_html)}
        </div>
    </div>

    <script>
        function showTab(tabId, btn) {{
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
            document.querySelector('.content').scrollTop = 0;
            window.scrollTo(0, 0);
            if (window.innerWidth <= 600) {{ closeMobileMenu(); }}
        }}

        function showSubTab(groupId, tabId, btn) {{
            // Find the parent panel
            var panel = btn.closest('.panel');
            panel.querySelectorAll('.sub-panel').forEach(p => p.style.display = 'none');
            panel.querySelectorAll('.sub-nav-item').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).style.display = 'block';
            btn.classList.add('active');
        }}

        function toggleMobileMenu() {{
            var sidebar = document.getElementById('sidebar');
            var overlay = document.getElementById('sidebarOverlay');
            var toggle = document.getElementById('menuToggle');
            var isOpen = sidebar.classList.contains('open');
            if (isOpen) {{
                sidebar.classList.remove('open');
                overlay.classList.remove('open');
                toggle.textContent = '☰';
            }} else {{
                sidebar.classList.add('open');
                overlay.classList.add('open');
                toggle.textContent = '✕';
            }}
        }}

        function closeMobileMenu() {{
            document.getElementById('sidebar').classList.remove('open');
            document.getElementById('sidebarOverlay').classList.remove('open');
            document.getElementById('menuToggle').textContent = '☰';
        }}

        window.addEventListener('resize', function() {{
            if (window.innerWidth > 600) {{
                closeMobileMenu();
            }}
        }});
    </script>
</body>
</html>'''

    with open(os.path.join(BASE, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written {len(html)} bytes to index.html')


if __name__ == '__main__':
    build_html()
