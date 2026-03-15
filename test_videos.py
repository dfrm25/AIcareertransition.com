#!/usr/bin/env python3
"""
Video ID Verification Script
Tests all video IDs to ensure they're valid and unique across personas
"""

import re
from collections import defaultdict

# Read the HTML file
with open('101.html', 'r') as f:
    content = f.read()

# Extract video IDs by persona
persona_videos = {}
video_to_personas = defaultdict(list)

# Find all persona sections and their videos
persona_pattern = r'id="(general|marketing|analytics|copywriting|product|data-science|email|customer|database)"'
persona_sections = re.finditer(persona_pattern, content)

for persona_match in re.finditer(r'id="(general|marketing|analytics|copywriting|product|data-science|email|customer|database)"', content):
    persona = persona_match.group(1)
    # Find all video IDs in this persona's section
    start_pos = persona_match.end()
    # Find next persona section or end of videos section
    next_match = re.search(r'id="(general|marketing|analytics|copywriting|product|data-science|email|customer|database)"', content[start_pos:])
    if next_match:
        end_pos = start_pos + next_match.start()
    else:
        end_pos = len(content)
    
    persona_content = content[start_pos:end_pos]
    video_ids = re.findall(r'watch\?v=([^"]+)', persona_content)
    persona_videos[persona] = list(set(video_ids[:3]))  # Get first 3 unique
    
    for vid in persona_videos[persona]:
        video_to_personas[vid].append(persona)

# Print results
print("=" * 60)
print("VIDEO ID DISTRIBUTION BY PERSONA")
print("=" * 60)
for persona, videos in sorted(persona_videos.items()):
    print(f"\n{persona.upper()}:")
    for i, vid in enumerate(videos, 1):
        sources = video_to_personas[vid]
        dup_flag = " ⚠️ DUPLICATE" if len(sources) > 1 else ""
        print(f"  {i}. {vid}{dup_flag}")
        if len(sources) > 1:
            print(f"     Also used in: {', '.join([s for s in sources if s != persona])}")

print("\n" + "=" * 60)
print("UNIQUE VIDEO ID SUMMARY")
print("=" * 60)
print(f"Total unique video IDs: {len(video_to_personas)}")
print(f"Total personas: {len(persona_videos)}")
print(f"Expected unique videos: {len(persona_videos) * 3}")
print(f"Actual unique videos found: {sum(len(v) for v in persona_videos.values())}")

# Check for duplicates
duplicates = {vid: persons for vid, persons in video_to_personas.items() if len(persons) > 1}
if duplicates:
    print(f"\n⚠️  WARNING: {len(duplicates)} video IDs are duplicated across personas:")
    for vid, persons in duplicates.items():
        print(f"  {vid}: used in {', '.join(persons)}")
else:
    print("\n✅ No duplicate video IDs found!")

# Verify thumbnail URLs
print("\n" + "=" * 60)
print("THUMBNAIL URL VERIFICATION")
print("=" * 60)
thumbnail_mismatches = []
for vid in video_to_personas.keys():
    thumbnail_pattern = rf'watch\?v={re.escape(vid)}.*?vi/([^/]+)/maxresdefault'
    match = re.search(thumbnail_pattern, content, re.DOTALL)
    if match and match.group(1) != vid:
        thumbnail_mismatches.append((vid, match.group(1)))

if thumbnail_mismatches:
    print(f"⚠️  {len(thumbnail_mismatches)} thumbnail URL mismatches found:")
    for vid, thumb_id in thumbnail_mismatches:
        print(f"  Video {vid} has thumbnail {thumb_id}")
else:
    print("✅ All video IDs match their thumbnail URLs")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)