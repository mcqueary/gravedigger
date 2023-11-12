import pytest

from graver.page import CemeteryPage, Page

mixed_urls = [
    "https://www.findagrave.com/cemetery/53514",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/cemetery/55276/memorial-search",
]

memorial_urls = [
    "https://www.findagrave.com/memorial/53514/john-smith",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/memorial/54321/",
]

cemetery_urls = [
    "https://www.findagrave.com/cemetery/55276",
    "https://www.findagrave.com/cemetery/153/",
]

list_urls = [
    "https://www.findagrave.com/cemetery/55276/memorial-search",
    "https://www.findagrave.com/cemetery/153/memorial-search?",
]


@pytest.mark.parametrize("url", mixed_urls)
def test_page_url(url):
    page = Page(url)
    assert page is not None
    assert page.url == url


# @pytest.mark.parametrize("url", mixed_urls)
# def test_page_type_not_none(url):
#     assert Page(url).type is not None


@pytest.mark.parametrize("url", cemetery_urls)
def test_cem_page(url):
    page = CemeteryPage(url)
    assert isinstance(page, CemeteryPage)
