"""YouTube upload metadata rules (youtube-agent-skill utillayer U9, MIT; written anew). Report-only list of issues.

  check(title, description, tags=(), duration_s=None, has_music=False, shorts=False) -> [ {code, detail} ]
"""
import re

HASHTAG = re.compile(r'(?<![\w&])#[^\s#]+')


def check(title, description, tags=(), duration_s=None, has_music=False, shorts=False):
    issues = []
    if len(title) > 100:
        issues.append(dict(code='title_too_long', detail=f'{len(title)} chars > 100'))
    size = len(description.encode('utf-8'))
    if size > 5000:
        issues.append(dict(code='description_too_long', detail=f'{size} bytes UTF-8 > 5000'))
    tags_in_desc = HASHTAG.findall(description)
    if len(tags_in_desc) > 60:
        issues.append(dict(code='hashtags_all_ignored', detail=f'{len(tags_in_desc)} hashtags > 60: YouTube ignores all of them'))
    elif len(tags_in_desc) > 3:
        issues.append(dict(code='hashtags_over_three', detail=f'{len(tags_in_desc)} hashtags: only the first 3 '
                           f'({" ".join(tags_in_desc[:3])}) show above the title'))
    if shorts and has_music and duration_s is not None and duration_s > 60:
        issues.append(dict(code='shorts_music_over_60s', detail=f'{duration_s:.1f} s Short with music: '
                           'a Content ID claim may block it worldwide'))
    return issues
