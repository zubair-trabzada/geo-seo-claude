"""
Tests for the optional live checks in brand_scanner.py (Scavio API).

The fixtures below are trimmed copies of real API responses captured on
2026-11-14. No test touches the network: requests.post and requests.get are
mocked.
"""

import sys
import os
from unittest.mock import patch, MagicMock

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import brand_scanner  # noqa: E402
from brand_scanner import (  # noqa: E402
    LiveCheckError,
    generate_brand_report,
    live_ai_answers,
    live_reddit_presence,
    live_youtube_presence,
    main,
)

API_KEY = "sk_test_do_not_leak"
PROMPT = "What are the best privacy-friendly web analytics tools for a small business website?"

YT_FATHOM = {'data': {'results': [{'type': 'video',
                       'video_id': 'K5lO7AMURA4',
                       'title': 'Fathom Analytics: Overview (Google Analytics Replacement)',
                       'url': 'https://www.youtube.com/watch?v=K5lO7AMURA4',
                       'view_count': 1190,
                       'published_time': '3 years ago',
                       'channel': {'id': 'UCVrbG75SpMfvIo0P0wkk8jw',
                                   'name': 'Convology',
                                   'url': 'https://www.youtube.com/channel/UCVrbG75SpMfvIo0P0wkk8jw'}},
                      {'type': 'video',
                       'video_id': 'w50IrwhzCEM',
                       'title': 'Fathom Analytics Dashboard Walk-through & Demo',
                       'url': 'https://www.youtube.com/watch?v=w50IrwhzCEM',
                       'view_count': 2369,
                       'published_time': '5 years ago',
                       'channel': {'id': 'UCh-bZHHOxxxSoiHDCfbxU_w',
                                   'name': 'Fathom Analytics',
                                   'url': 'https://www.youtube.com/channel/UCh-bZHHOxxxSoiHDCfbxU_w'}},
                      {'type': 'video',
                       'video_id': 'puemALIAd5M',
                       'title': 'Fathom Analytics vs Google Analytics – Why I Switched for Privacy',
                       'url': 'https://www.youtube.com/watch?v=puemALIAd5M',
                       'view_count': 323,
                       'published_time': '1 year ago',
                       'channel': {'id': 'UCKQiq3DspqmiIDMvO2gkobw',
                                   'name': 'Purpose & Pixel',
                                   'url': 'https://www.youtube.com/channel/UCKQiq3DspqmiIDMvO2gkobw'}},
                      {'type': 'video',
                       'video_id': 'F561egK5vMY',
                       'title': 'Plausible Analytics vs Fathom Analytics | 2025 Comparison & '
                                'Review',
                       'url': 'https://www.youtube.com/watch?v=F561egK5vMY',
                       'view_count': 305,
                       'published_time': '1 year ago',
                       'channel': {'id': 'UCd0TeNQlsYJdeIDtMXrg3lA',
                                   'name': "Jake's Tech Lab",
                                   'url': 'https://www.youtube.com/channel/UCd0TeNQlsYJdeIDtMXrg3lA'}},
                      {'type': 'video',
                       'video_id': 'p-5fpCjKplg',
                       'title': 'Creating simple events in Fathom Analytics',
                       'url': 'https://www.youtube.com/watch?v=p-5fpCjKplg',
                       'view_count': 2443,
                       'published_time': '2 years ago',
                       'channel': {'id': 'UCh-bZHHOxxxSoiHDCfbxU_w',
                                   'name': 'Fathom Analytics',
                                   'url': 'https://www.youtube.com/channel/UCh-bZHHOxxxSoiHDCfbxU_w'}}],
          'shorts': [],
          'channels': [{'channel_id': 'UCh-bZHHOxxxSoiHDCfbxU_w',
                        'name': 'Fathom Analytics',
                        'handle': None,
                        'url': 'https://www.youtube.com/channel/UCh-bZHHOxxxSoiHDCfbxU_w',
                        'subscriber_count': 652}],
          'playlists': []},
 'credits_used': 2}

YT_PLAUSIBLE = {'data': {'results': [{'type': 'video',
                       'video_id': 'nImTI8u5JLk',
                       'title': 'Deep dive into Plausible analytics, a Google Analytics competitor',
                       'url': 'https://www.youtube.com/watch?v=nImTI8u5JLk',
                       'view_count': 9497,
                       'published_time': '4 years ago',
                       'channel': {'id': 'UCGYdWR8QUYn88lG0PBeJQ_g',
                                   'name': 'A Better Computer',
                                   'url': 'https://www.youtube.com/channel/UCGYdWR8QUYn88lG0PBeJQ_g'}},
                      {'type': 'video',
                       'video_id': 'P0T6VjTS7_Y',
                       'title': 'DITCH Google Analytics. Use Plausible on your website!',
                       'url': 'https://www.youtube.com/watch?v=P0T6VjTS7_Y',
                       'view_count': 13253,
                       'published_time': '5 years ago',
                       'channel': {'id': 'UCjSEJkpGbcZhvo0lr-44X_w',
                                   'name': 'TechHut',
                                   'url': 'https://www.youtube.com/channel/UCjSEJkpGbcZhvo0lr-44X_w'}},
                      {'type': 'video',
                       'video_id': '6xXSsu0YXWo',
                       'title': 'Google Analytics Is Dead',
                       'url': 'https://www.youtube.com/watch?v=6xXSsu0YXWo',
                       'view_count': 111340,
                       'published_time': '2 years ago',
                       'channel': {'id': 'UCbRP3c757lWg9M-U7TyEkXA',
                                   'name': 'Theo - t3․gg',
                                   'url': 'https://www.youtube.com/channel/UCbRP3c757lWg9M-U7TyEkXA'}}],
          'shorts': [],
          'channels': [],
          'playlists': []},
 'credits_used': 2}

REDDIT_PLAUSIBLE = {'data': {'results': [{'post_id': 't3_1up6xes',
                       'title': 'plausible analytics enshittification - alternatives? db '
                                'migration?',
                       'text': 'when did the plausible enshittified and locked sampling behind '
                               'enterprise license?  \n'
                               "I'm surprised this wasn't a bigger story.  "
                               '[https://github.com/plausible/analytics/discussions/4285](https://github',
                       'url': 'https://www.reddit.com/r/selfhosted/comments/1up6xes/plausible_analytics_enshittification_alternatives/',
                       'subreddit': 'selfhosted',
                       'score': 3,
                       'num_comments': 22,
                       'created_at': '2026-07-06T19:05:37.882000+0000'},
                      {'post_id': 't3_1so7ior',
                       'title': 'Plausible pricing plans',
                       'text': 'I’ve been with Plausible analytics for 2.5 years now. I originally '
                               'joined and paid because ga was the only cookie being added to the '
                               'site and would do anything not to have a cookie noticed. We '
                               'recentl',
                       'url': 'https://www.reddit.com/r/analytics/comments/1so7ior/plausible_pricing_plans/',
                       'subreddit': 'analytics',
                       'score': 2,
                       'num_comments': 5,
                       'created_at': '2026-04-17T17:23:57.146000+0000'},
                      {'post_id': 't3_1qtp89u',
                       'title': 'Free alternatives to GA4 / Plausible ?',
                       'text': 'I know google analytics si good and free, but I’m looking for an '
                               'alternative more simpler (like plausible) because I don’t know '
                               'much about this, so I want to start simple.\n'
                               '\n'
                               'Self hosting a solution is ',
                       'url': 'https://www.reddit.com/r/SaaS/comments/1qtp89u/free_alternatives_to_ga4_plausible/',
                       'subreddit': 'SaaS',
                       'score': 4,
                       'num_comments': 32,
                       'created_at': '2026-02-02T08:09:31.501000+0000'}]},
 'credits_used': 1}

CHATGPT_ANALYTICS = {'data': {'platform': 'chatgpt',
          'prompt': 'What are the best privacy-friendly web analytics tools for a small business '
                    'website?',
          'model': 'gpt-6',
          'answer': {'markdown': '**My top recommendations for 2026 are Plausible, Fathom, Umami, '
                                 'Matomo, and Simple Analytics.**\n'
                                 '\n'
                                 '## Best privacy-friendly analytics tools\n'
                                 '\n'
                                 '\n'
                                 '**1\\. Plausible Analytics**\n'
                                 '\n'
                                 '(Best overall)\n'
                                 '\n'
                                 'Hosted and open-source options\n'
                                 '\n'
                                 '- Cookie-free tracking by default.\n'
                                 '- No traditional visitor profiling.\n'
                                 '- Clear dashboards for pageviews, referrals, campaigns and '
                                 'goals.\n'
                                 '- EU-based data hosting.\n'
                                 '- Lightweight trackin'},
          'sources': [{'url': 'https://umami.is/pricing?utm_source=chatgpt.com',
                       'title': 'Pricing',
                       'snippet': None,
                       'source': 'Umami',
                       'published_at': None},
                      {'url': 'https://plausible.io/?utm_source=chatgpt.com',
                       'title': 'plausible.io',
                       'snippet': None,
                       'source': 'plausible.io',
                       'published_at': None},
                      {'url': 'https://usefathom.com/?utm_source=chatgpt.com',
                       'title': 'usefathom.com',
                       'snippet': None,
                       'source': 'usefathom.com',
                       'published_at': None}],
          'search_queries': ['best privacy friendly web analytics tools 2026 Plausible Fathom '
                             'Umami Matomo Simple Analytics pricing features'],
          'shopping': []},
 'credits_used': 2}

AI_MODE_ANALYTICS = {'search_parameters': {'q': 'best privacy-friendly web analytics tools for a small business '
                            'website',
                       'hl': 'en',
                       'gl': 'us',
                       'device': 'desktop',
                       'google_domain': 'google.com'},
 'text_blocks': [{'type': 'paragraph',
                  'snippet': 'The best privacy-friendly web analytics tools for a small business '
                             'are Plausible Analytics, Fathom Analytics, Simple Analytics, Matomo, '
                             'and Cloudflare Web Analytics. These platforms avoid invasive cro'},
                 {'type': 'list',
                  'list': [{'snippet': 'Fathom Analytics Best for: Businesses looking for a '
                                       'reliable, "set-it-and-forget-it" Google Analytics '
                                       'alternative. Privacy & Hosting: Fully GDPR, CCPA, '
                                       'ePrivacy, and PECR compliant with EU traffic routed '
                                       'through European servers. Key Features: Offers cookieless '
                                       'pageview tracking, custom conversion e'}]},
                 {'type': 'table',
                  'table_headers': ['Tool',
                                    'Best For',
                                    'Hosting Model',
                                    'Cookieless?',
                                    'Starting Price'],
                  'table_rows': [['Plausible',
                                  'Best overall balance of simplicity & features',
                                  'Cloud (EU) or Self-Hosted',
                                  'Yes',
                                  '$9/mo (or Free self-hosted)'],
                                 ['Fathom',
                                  'Effortless setup & unlimited retention',
                                  'Cloud (EU routing)',
                                  'Yes',
                                  '$15/mo']]}],
 'references': [{'title': 'Fathom Analytics: Privacy-First Google Analytics Alternative',
                 'link': 'https://usefathom.com/',
                 'source': 'Fathom Analytics',
                 'index': 0},
                {'title': 'Plausible Analytics | Simple, privacy-friendly Google Analytics '
                          'alternative',
                 'link': 'https://plausible.io/',
                 'source': 'Plausible Analytics',
                 'index': 2},
                {'title': 'Best privacy‑friendly analytics for static sites - Reddit',
                 'link': 'https://www.reddit.com/r/statichosting/comments/1oh0ds5/best_privacyfriendly_analytics_for_static_sites/',
                 'source': 'Reddit',
                 'index': 3}],
 'credits_used': 1}


def _response(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    return resp


def _wikipedia_get(*args, **kwargs):
    return _response({"query": {"search": []}, "search": []})


class TestOptIn:
    def test_no_key_keeps_the_offline_report(self):
        with patch.object(brand_scanner.requests, "post") as post, \
                patch.object(brand_scanner.requests, "get", side_effect=_wikipedia_get):
            report = generate_brand_report("Fathom", "usefathom.com", prompts=[PROMPT])
        post.assert_not_called()
        assert "live" not in report["platforms"]["youtube"]
        assert "ai_answers" not in report
        assert "live_credits_used" not in report
        assert report["platforms"]["youtube"]["check_instructions"]

    def test_live_flag_without_key_exits_with_error(self, monkeypatch, capsys):
        monkeypatch.delenv("SCAVIO_API_KEY", raising=False)
        with patch.object(brand_scanner.requests, "post") as post:
            assert main(["Fathom", "--live"]) == 1
        post.assert_not_called()
        assert "SCAVIO_API_KEY" in capsys.readouterr().err

    def test_key_alone_does_not_turn_on_live_checks(self, monkeypatch, capsys):
        monkeypatch.setenv("SCAVIO_API_KEY", API_KEY)
        monkeypatch.delenv("GEO_LIVE_PROVIDER", raising=False)
        with patch.object(brand_scanner.requests, "post") as post, \
                patch.object(brand_scanner.requests, "get", side_effect=_wikipedia_get):
            assert main(["Fathom", "usefathom.com"]) == 0
        post.assert_not_called()
        assert '"live"' not in capsys.readouterr().out

    def test_env_opt_in_runs_live_checks(self, monkeypatch, capsys):
        monkeypatch.setenv("SCAVIO_API_KEY", API_KEY)
        monkeypatch.setenv("GEO_LIVE_PROVIDER", "scavio")
        replies = [_response(YT_FATHOM), _response(REDDIT_PLAUSIBLE)]
        with patch.object(brand_scanner.requests, "post", side_effect=replies) as post, \
                patch.object(brand_scanner.requests, "get", side_effect=_wikipedia_get):
            assert main(["Fathom", "usefathom.com"]) == 0
        assert post.call_count == 2
        out = capsys.readouterr().out
        assert '"live_credits_used": 3' in out
        assert API_KEY not in out


class TestYouTube:
    def test_request_shape(self):
        with patch.object(brand_scanner.requests, "post", return_value=_response(YT_FATHOM)) as post:
            live_youtube_presence("Fathom Analytics", API_KEY)
        args, kwargs = post.call_args
        assert args[0] == "https://api.scavio.dev/api/v1/youtube/search"
        assert kwargs["json"] == {"search": "Fathom Analytics"}
        assert kwargs["headers"]["Authorization"] == f"Bearer {API_KEY}"
        assert API_KEY not in args[0]

    def test_brand_channel_and_third_party_videos(self):
        with patch.object(brand_scanner.requests, "post", return_value=_response(YT_FATHOM)):
            live = live_youtube_presence("Fathom Analytics", API_KEY)
        assert live["brand_channel"]["name"] == "Fathom Analytics"
        assert live["brand_channel"]["subscribers"] == 652
        assert live["videos_returned"] == 5
        assert live["videos_mentioning_brand"] == 5
        assert live["videos_from_brand_channel"] == 2
        assert live["third_party_channels"] == 3
        assert live["top_videos"][0]["view_count"] is not None

    def test_no_brand_channel(self):
        with patch.object(brand_scanner.requests, "post", return_value=_response(YT_PLAUSIBLE)):
            live = live_youtube_presence("Plausible", API_KEY)
        assert live["brand_channel"] is None
        # The third video ("Google Analytics Is Dead") does not name the brand.
        assert live["videos_returned"] == 3
        assert live["videos_mentioning_brand"] == 2


class TestReddit:
    def test_mentions_subreddits_and_dates(self):
        with patch.object(brand_scanner.requests, "post", return_value=_response(REDDIT_PLAUSIBLE)) as post:
            live = live_reddit_presence("Plausible", API_KEY)
        assert post.call_args[0][0] == "https://api.scavio.dev/api/v1/reddit/search"
        assert post.call_args[1]["json"] == {"query": "Plausible"}
        assert live["posts_mentioning_brand"] == 3
        assert live["subreddits"] == {"selfhosted": 1, "analytics": 1, "SaaS": 1}
        assert live["brand_subreddit"] is False
        assert live["newest_mention"] == "2026-07-06"
        assert live["oldest_mention"] == "2026-02-02"
        assert live["total_comments"] == 22 + 5 + 32

    def test_whole_word_match_only(self):
        assert brand_scanner._mentions("Plausible vs Google analytics", "Plausible")
        assert not brand_scanner._mentions("That sounds plausibly fine", "Plausible")


class TestAiAnswers:
    def test_mentions_and_citations_per_engine(self):
        replies = [_response(CHATGPT_ANALYTICS), _response(AI_MODE_ANALYTICS)]
        with patch.object(brand_scanner.requests, "post", side_effect=replies) as post:
            result = live_ai_answers("Fathom", "https://www.usefathom.com/", [PROMPT], API_KEY)
        paths = [c[0][0] for c in post.call_args_list]
        assert paths == [
            "https://api.scavio.dev/api/v1/chatgpt/prompt",
            "https://api.scavio.dev/api/v2/google/ai-mode",
        ]
        assert post.call_args_list[0][1]["json"] == {"prompt": PROMPT}
        assert post.call_args_list[1][1]["json"] == {"query": PROMPT}
        entry = result["prompts"][0]
        assert entry["chatgpt"] == {"mentions_brand": True, "cites_domain": True, "sources": 3}
        assert entry["google_ai_mode"] == {"mentions_brand": True, "cites_domain": True, "sources": 3}
        assert result["summary"]["chatgpt"] == {"prompts_answered": 1, "brand_mentioned": 1, "domain_cited": 1}
        assert result["credits"] == 3

    def test_brand_absent_from_answers(self):
        replies = [_response(CHATGPT_ANALYTICS), _response(AI_MODE_ANALYTICS)]
        with patch.object(brand_scanner.requests, "post", side_effect=replies):
            result = live_ai_answers("Acme Metrics", "acmemetrics.com", [PROMPT], API_KEY)
        assert result["summary"]["chatgpt"]["brand_mentioned"] == 0
        assert result["summary"]["google_ai_mode"]["domain_cited"] == 0

    def test_ai_mode_tables_and_lists_are_read(self):
        data = {"text_blocks": [
            {"type": "list", "list": [{"snippet": "Simple first item"}]},
            {"type": "table", "table_headers": ["Tool"], "table_rows": [["Rybbit"]]},
        ]}
        text = brand_scanner._ai_mode_text(data)
        assert "Simple first item" in text and "Rybbit" in text

    def test_subdomain_citation_counts(self):
        assert brand_scanner._cites_domain(["https://ingest.plausible.io/x"], "plausible.io")
        assert not brand_scanner._cites_domain(["https://notplausible.io/"], "plausible.io")

    def test_prompts_are_capped(self):
        prompts = [f"question {i}" for i in range(12)]
        replies = [_response(CHATGPT_ANALYTICS), _response(AI_MODE_ANALYTICS)] * 10
        with patch.object(brand_scanner.requests, "post", side_effect=replies) as post:
            result = live_ai_answers("Fathom", "usefathom.com", prompts, API_KEY)
        assert post.call_count == 20
        assert result["skipped_prompts"] == 2
        assert result["credits"] == 30


class TestErrors:
    @pytest.mark.parametrize("status", [401, 402, 429, 500])
    def test_http_errors_are_reported_once_without_the_key(self, status):
        with patch.object(brand_scanner.requests, "post", return_value=_response({"error": "x"}, status)) as post:
            with pytest.raises(LiveCheckError) as exc:
                live_reddit_presence("Plausible", API_KEY)
        assert post.call_count == 1
        assert f"HTTP {status}" in str(exc.value)
        assert API_KEY not in str(exc.value)

    def test_timeout(self):
        with patch.object(brand_scanner.requests, "post", side_effect=requests.Timeout()):
            with pytest.raises(LiveCheckError, match="timeout"):
                live_youtube_presence("Fathom", API_KEY)

    def test_failed_live_check_keeps_the_offline_result(self):
        replies = [_response({"error": "x"}, 402), _response(REDDIT_PLAUSIBLE)]
        with patch.object(brand_scanner.requests, "post", side_effect=replies), \
                patch.object(brand_scanner.requests, "get", side_effect=_wikipedia_get):
            report = generate_brand_report("Plausible", "plausible.io", api_key=API_KEY)
        youtube = report["platforms"]["youtube"]
        assert "HTTP 402" in youtube["live_error"]
        assert youtube["check_instructions"]
        assert report["platforms"]["reddit"]["live"]["posts_mentioning_brand"] == 3
        assert report["live_credits_used"] == 1

    def test_one_engine_failing_does_not_drop_the_other(self):
        replies = [_response({"error": "x"}, 500), _response(AI_MODE_ANALYTICS)]
        with patch.object(brand_scanner.requests, "post", side_effect=replies):
            result = live_ai_answers("Fathom", "usefathom.com", [PROMPT], API_KEY)
        assert "HTTP 500" in result["prompts"][0]["chatgpt"]["error"]
        assert result["prompts"][0]["google_ai_mode"]["mentions_brand"] is True
        assert result["summary"]["chatgpt"]["prompts_answered"] == 0
        # The failed ChatGPT call is not charged; only AI Mode's credit counts.
        assert result["credits"] == 1
