import pytest

from helpers import build_ydl_format, clean_filename, detect_platform, is_http_url


@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=abc", "youtube"),
    ("https://youtu.be/abc", "youtube"),
    ("https://x.com/user/status/1", "twitter"),
    ("https://mobile.twitter.com/u", "twitter"),
    ("https://www.netflix.com/title/1", "unknown"),  # 'x.com' substring must not match
    ("https://evil.com/?u=youtube.com", "unknown"),
    ("https://notyoutube.com/x", "unknown"),
    ("not a url", "unknown"),
])
def test_detect_platform(url, expected):
    assert detect_platform(url) == expected


def test_is_http_url():
    assert is_http_url("https://youtu.be/a")
    assert not is_http_url("file:///etc/passwd")
    assert not is_http_url("javascript:alert(1)")


def test_clean_filename():
    assert clean_filename('a/b:c*"d') == "abcd"
    assert clean_filename("  hello   world ") == "hello_world"
    assert clean_filename("") == "download"
    assert len(clean_filename("x" * 500)) == 100


def test_resolution_is_a_ceiling():
    assert "[height<=720]" in build_ydl_format("mkv", "720")["format"]
    assert "height" not in build_ydl_format("mkv", "best")["format"]


def test_mp4_has_fallbacks_and_no_reencode_postprocessors():
    o = build_ydl_format("mp4", "1080")
    assert o["format"].endswith("/best[height<=1080]")
    assert o["merge_output_format"] == "mp4"
    assert "postprocessors" not in o


def test_avi_not_capped_at_720():
    assert "720" not in build_ydl_format("avi", "best")["format"]


def test_audio_quality_only_for_lossy():
    assert build_ydl_format("mp3", "best")["postprocessors"][0]["preferredquality"] == "192"
    assert "preferredquality" not in build_ydl_format("flac", "best")["postprocessors"][0]


def test_unsupported_format():
    with pytest.raises(ValueError):
        build_ydl_format("exe", "best")
