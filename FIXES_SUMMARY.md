# Fixes Summary - Videos & Blog

## Problem 1: Duplicate Videos in 101.html
**Issue**: Nearly all personas use the same 3 video IDs (G2fqAlgmoPo, zizonToFXDs, w_3L1Bf2P_g) with different labels.

**Solution**: Replace with unique, persona-specific videos from official Google Cloud sources. Each persona should have 3 unique videos that aren't duplicated across other personas.

## Problem 2: Fake Blog Posts in blog.html  
**Issue**: All 9 blog posts are placeholder/fake content.

**Solution**: Replace all fake blog posts with ONE real blog post about prompting best practices:
- Title: "5 Prompting Best Practices That Actually Work"
- 2 paragraphs (human-written, practical, actionable)
- Visual element (infographic-style)
- Category: Prompt Engineering
- Date: January 10, 2026
- Read time: ~3-4 min read

## Files to Update:
1. `101.html` - Replace video sections for Marketing, Copywriting, Analytics, Data Science, Product, Email, Customer Journey, Database Marketing with unique video IDs
2. `blog.html` - Replace Featured Post and all 9 blog posts with single real blog post

## Notes:
- All videos must be from official Google Cloud, Microsoft, OpenAI, or Anthropic sources
- No influencer content
- Each persona must have 3 unique videos not duplicated elsewhere
- Blog post must read naturally and provide practical value
