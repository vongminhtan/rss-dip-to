import json
import os

file_path = "/Users/tanvong/rss-dip-to/ket_qua/bao_cao_2026-02-07.txt"
error_links = []

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for entry in data:
            content = entry.get("noi_dung")
            if not content or content == "Không thể bóc tách nội dung." or content.strip() == "":
                error_links.append(entry.get("duong_dan"))
except Exception as e:
    print(f"Error reading file: {e}")

if error_links:
    print(f"Total error links: {len(error_links)}")
    # Print unique domains to see patterns
    from collections import Counter
    domains = [link.split('/')[2] if '://' in link else link for link in error_links]
    domain_counts = Counter(domains)
    print("\nError counts by domain:")
    for domain, count in domain_counts.items():
        print(f"- {domain}: {count}")
    
    print("\nFull list of error links:")
    for link in error_links:
        print(link)
else:
    print("No error links found.")
