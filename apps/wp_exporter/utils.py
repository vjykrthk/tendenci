import datetime, encoder
from django.conf import settings
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from site_settings.utils import get_setting
from categories.models import Category
from pages.models import Page
from articles.models import Article
from news.models import News
from events.models import Event
from jobs.models import Job
from resumes.models import Resume
    

def gen_xml(data):
    """
    Makes use of the encoder for xml to generate the wordpress export.
    """
    xml = encoder.XML()
    xml.write(
        '<rss version="2.0"\n' +
        '   xmlns:excerpt="http://wordpress.org/export/1.0/excerpt/"\n' +
        '   xmlns:content="http://purl.org/rss/1.0/modules/content/"\n' +
        '   xmlns:wfw="http://wellformedweb.org/CommentAPI/"\n' +
        '   xmlns:dc="http://purl.org/dc/elements/1.1/"\n' +
        '   xmlns:wp="http://wordpress.org/export/1.0/"\n' +
        '>'
    )
    xml.open("channel")
    encode_site(xml)
    offset = 0
    if data["pages"]:
        offset = encode_pages(xml, offset)
    if data["articles"]:
        offset = encode_articles(xml, offset)
    if data["news"]:
        offset = encode_news(xml, offset)
    if data["jobs"]:
        offset = encode_jobs(xml, offset)
    if data["events"]:
        offset = encode_events(xml, offset)
    if data["case_studies"]:
        offset = encode_casestudies(xml, offset)
    if data["resumes"]:
        offset = encode_resumes(xml, offset)
    xml.close("channel")
    xml.close("rss")
    return xml

def encode_site(xml):
    xml.write("<title>%s</title>"%get_setting('site', 'global', 'sitedisplayname'), depth=1)
    xml.write("<description></description>", depth=1)
    xml.write("<pubDate>%s</pubDate>"%datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), depth=1)
    xml.write("<language>%s</language>"%get_setting('site', 'global', 'localizationlanguage'), depth=1)
    xml.write("<wp:wxr_version>%s</wp:wxr_version>"%1.0, depth=1)
    # not sure if this is required
    #xml.write("<wp:base_site_url>http://wordpress.com/</wp:base_site_url>", depth=1)
    #xml.write("<wp:base_blog_url>http://sambixly.wordpress.com</wp:base_blog_url>", depth=1)
    encode_categories(xml)
    
def encode_categories(xml):
    # since wordpress categories can only have single parents,
    # I will be not be associating the categories with any parents.
    ct_page = ContentType.objects.get_for_model(Page)
    ct_article = ContentType.objects.get_for_model(Article)
    ct_news = ContentType.objects.get_for_model(News)
    ct_job = ContentType.objects.get_for_model(Job)
    ct_event = ContentType.objects.get_for_model(Event)
    ct_resume = ContentType.objects.get_for_model(Resume)
    try:
        from case_studies.models import CaseStudy
        ct_casestudy = ContentType.objects.get_for_model(CaseStudy)
    except ImportError:
        ct_casestudy = None
    
    #encode tendenci categories
    cats = Category.objects.filter(
        Q(categoryitem_category__content_type=ct_page) or
        Q(categoryitem_category__content_type=ct_article) or
        Q(categoryitem_category__content_type=ct_news) or
        Q(categoryitem_category__content_type=ct_job) or
        Q(categoryitem_category__content_type=ct_event)).distinct()
    for cat in cats:
        xml.open("wp:category", depth=1)
        xml.write("<wp:category_nicename>%s</wp:category_nicename>"%slugify(cat.name), depth=2)
        xml.write("<wp:category_parent></wp:category_parent>", depth=2)
        xml.write("<wp:cat_name><![CDATA[%s]]></wp:cat_name>"%cat.name, depth=2)
        xml.close("wp:category", depth=1)
        
    #encode content types as categories
    types = [ct_article, ct_job, ct_event, ct_news, ct_page, ct_resume, ct_casestudy]
    for type in types:
        if type:
            xml.open("wp:category", depth=1)
            xml.write("<wp:category_nicename>%s</wp:category_nicename>"%slugify(type), depth=2)
            xml.write("<wp:category_parent></wp:category_parent>", depth=2)
            xml.write("<wp:cat_name><![CDATA[%s]]></wp:cat_name>"%type, depth=2)
            xml.close("wp:category", depth=1)

def encode_tags(xml):
    for tag in tags:
        xml.open("wp:tag", depth=1)
        xml.open("wp:tag_slug", depth=2)
        xml.write(slugify(tag), depth=3)
        xml.close("wp:tag_slug", depth=2)
        xml.open("wp:tag_name", depth=2)
        xml.write("<![CDATA[%s]]>"%tag, depth=3)
        xml.close("wp:tag_name", depth=2)
        xml.close("wp:tag", depth=1)
        
def encode_item(xml, offset, item, ct, title="", content=""):
    xml.open("item", depth=1)
    xml.write("<title>%s</title>"%title, depth=2)
    xml.write("<pubDate>%s</pubDate>"%item.create_dt.strftime("%a, %d %b %Y %H:%M:%S %z"), depth=2)
    xml.write("<dc:creator><![CDATA[%s]]></dc:creator>"%item.creator_username, depth=2)
    
    #get all the item's categories
    cats = Category.objects.filter(
        categoryitem_category__object_id = item.id,
        categoryitem_category__content_type = ct)
    
    #encode item's categories
    for cat in cats:
        xml.write("<category><![CDATA[%s]]></category>"%cat.name, depth=2)
        xml.write('<category domain="category" nicename="%s"><![CDATA[%s]]></category>' \
            % (slugify(cat.name),cat.name), depth=2)
        
    #encode ct as category
    xml.write("<category><![CDATA[%s]]></category>"%ct, depth=2)
    xml.write('<category domain="category" nicename="%s"><![CDATA[%s]]></category>' \
            % (slugify(ct),ct), depth=2)
    
    xml.write("<description></description>", depth=2)
    xml.write("<content:encoded><![CDATA[%s]]></content:encoded>"%content, depth=2)
    xml.write("<excerpt:encoded><![CDATA[]]></excerpt:encoded>", depth=2)
    xml.write("<wp:post_id>%s</wp:post_id>" % offset, depth=2)
    xml.write("<wp:post_date>%s</wp:post_date>"%item.create_dt, depth=2)
    xml.write("<wp:post_date_gmt>%s</wp:post_date_gmt>"%item.create_dt, depth=2)
    xml.write("<wp:comment_status>open</wp:comment_status>", depth=2)
    xml.write("<wp:ping_status>open</wp:ping_status>", depth=2)
    xml.write("<wp:post_name>%s</wp:post_name>"%slugify(title), depth=2)
    xml.write("<wp:status>publish</wp:status>", depth=2)
    xml.write("<wp:post_parent>0</wp:post_parent>", depth=2)
    xml.write("<wp:menu_order>0</wp:menu_order>", depth=2)
    xml.write("<wp:post_type>post</wp:post_type>", depth=2)
    xml.write("<wp:post_password></wp:post_password>", depth=2)
    xml.write("<wp:is_sticky>0</wp:is_sticky>", depth=2)
    xml.close("item", depth=1)
    
def encode_pages(xml, offset=0):
    pages = Page.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(Page)
    for page in pages:
        offset = offset+1
        encode_item(xml, offset, page, ct, title=page.title, content=page.content)
    return offset
        
def encode_articles(xml, offset=0):
    articles = Article.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(Article)
    for article in articles:
        offset = offset+1
        encode_item(xml, offset, article, ct, title=article.headline, content=article.body)
    return offset
        
def encode_news(xml, offset=0):
    newss = News.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(News)
    for news in newss:
        offset = offset+1
        encode_item(xml, offset, news, ct, title=news.headline, content=news.body)
    return offset
        
def encode_jobs(xml, offset=0):
    jobs = Job.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(Job)
    for job in jobs:
        offset = offset+1
        encode_item(xml, offset, job, ct, title=job.title, content=job.description)
    return offset
        
def encode_events(xml, offset=0):
    events = Event.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(Event)
    for event in events:
        offset = offset+1
        encode_item(xml, offset, event, ct, title=event.title, content=event.description)
    return offset
        
def encode_resumes(xml, offset=0):
    resumes = Resume.objects.filter(status=True)
    ct = ContentType.objects.get_for_model(Resume)
    for resume in resumes:
        offset = offset+1
        encode_item(xml, offset, resume, ct, title=resume.title, content=resume.description)
    return offset

def encode_casestudies(xml, offset=0):
    try:
        from case_studies.models import CaseStudy
        studies = CaseStudy.objects.filter(status=True)
        ct = ContentType.objects.get_for_model(CaseStudy)
        for study in studies:
            offset = offset+1
            encode_item(xml, offset, study, ct, title=study.client, content=study.overview)
    except ImportError:
        pass
    return offset
